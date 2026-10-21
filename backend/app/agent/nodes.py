import json
import logging
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from app.agent.prompts import build_system_prompt
from app.agent.state import AgentState
from app.config import settings
from app.tools import ALL_TOOLS, WRITE_TOOL_NAMES

logger = logging.getLogger(__name__)

# LLM with prompt caching on system message
llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    api_key=settings.anthropic_api_key,
    temperature=0.3,
    max_tokens=1024,
).bind_tools(ALL_TOOLS)

# Handles actual tool execution
tool_node = ToolNode(ALL_TOOLS)


async def agent_node(state: AgentState) -> AgentState:
    """
    Main reasoning node. Claude reads conversation + decides what to do.
    If it picks a write tool, we intercept before execution.
    """
    system = SystemMessage(
        content=[
            {
                "type": "text",
                "text": build_system_prompt(),
                "cache_control": {"type": "ephemeral"},  # prompt caching
            }
        ]
    )

    response = await llm.ainvoke([system] + state["messages"])
    return {"messages": [response], "pending_action": None, "confirmed": None}


async def confirm_node(state: AgentState) -> AgentState:
    """
    Intercepts write tool calls. Extracts the pending action,
    replaces the tool_use message with a plain confirmation request
    (so Anthropic doesn't see an orphaned tool_use block).
    """
    last_message: AIMessage = state["messages"][-1]
    tool_calls = last_message.tool_calls

    if not tool_calls:
        return state

    # Find the first write tool call
    write_call = next(
        (tc for tc in tool_calls if tc["name"] in WRITE_TOOL_NAMES), None
    )

    if not write_call:
        return state

    # Build human-readable summary for confirmation
    name = write_call["name"]
    args = write_call["args"]
    summary = _build_confirmation_summary(name, args)

    # IMPORTANT: Replace the tool_use AIMessage with the SAME ID but no tool_calls.
    # add_messages deduplicates by ID, so returning the same ID replaces the message.
    # This prevents "tool_use without tool_result" error on the next Anthropic call.
    confirmation_message = AIMessage(
        id=last_message.id,  # same ID = replace, not append
        content=f"{summary} Shall I go ahead?",
    )

    return {
        "messages": [confirmation_message],
        "pending_action": {
            "tool_name": name,
            "tool_call_id": write_call["id"],
            "args": args,
            "summary": summary,
        },
        "confirmed": None,
    }


async def execute_confirmed_node(state: AgentState) -> AgentState:
    """Execute the confirmed pending action directly (without ToolNode)."""
    pending = state.get("pending_action")
    if not pending:
        return state

    # Find and call the tool directly
    tool_name = pending["tool_name"]
    tool_args = pending["args"]

    target_tool = next((t for t in ALL_TOOLS if t.name == tool_name), None)
    if not target_tool:
        follow_up = AIMessage(content=f"Sorry, I couldn't find the tool to execute that action.")
        return {"messages": [follow_up], "pending_action": None, "confirmed": None}

    try:
        result = await target_tool.ainvoke(tool_args)
        follow_up = AIMessage(content=f"Done! {result}")
    except Exception as e:
        follow_up = AIMessage(content=f"Sorry, there was an error: {str(e)}")

    return {
        "messages": [follow_up],
        "pending_action": None,
        "confirmed": None,
    }


async def cancel_node(state: AgentState) -> AgentState:
    """User cancelled the pending action."""
    return {
        "messages": [AIMessage(content="No problem, I've cancelled that. Anything else?")],
        "pending_action": None,
        "confirmed": None,
    }


def _build_confirmation_summary(tool_name: str, args: dict) -> str:
    """Build a plain-English confirmation summary for write actions."""
    if tool_name == "create_event":
        attendees = args.get("attendee_emails", [])
        invite_str = f" and send an invite to {', '.join(attendees)}" if attendees else ""
        return (
            f"I'll create '{args.get('title')}' from {args.get('start_iso')} "
            f"to {args.get('end_iso')}{invite_str}."
        )
    elif tool_name == "update_event":
        changes = {k: v for k, v in args.items() if k != "event_id" and v}
        change_str = ", ".join(f"{k}: {v}" for k, v in changes.items())
        return f"I'll update the event with these changes: {change_str}."
    elif tool_name == "delete_event":
        return f"I'll delete event with ID {args.get('event_id')}."
    elif tool_name == "create_meal_calendar_events":
        days = args.get("days", 7)
        start = args.get("start_date", "today")
        return f"I'll add the next {days} days of meal plan to your Google Calendar starting {start}."
    return f"I'll run {tool_name} with {json.dumps(args)}."


# ── Routing functions ────────────────────────────────────────────────────────

def should_confirm(state: AgentState) -> Literal["confirm", "tools", "end"]:
    """After agent_node: route to confirm if write tool, tools if read tool, end otherwise."""
    last: AIMessage = state["messages"][-1]
    if not hasattr(last, "tool_calls") or not last.tool_calls:
        return "end"

    tool_names = {tc["name"] for tc in last.tool_calls}

    if tool_names & WRITE_TOOL_NAMES:
        return "confirm"
    return "tools"


def after_confirm(state: AgentState) -> Literal["execute", "cancel", "wait"]:
    """After confirm_node: route based on whether user has responded."""
    confirmed = state.get("confirmed")
    if confirmed is True:
        return "execute"
    elif confirmed is False:
        return "cancel"
    return "wait"  # waiting for user input — graph pauses here
