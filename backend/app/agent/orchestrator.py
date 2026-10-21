import logging
from fastapi import WebSocket
from langchain_core.messages import HumanMessage, AIMessage

from app.agent.graph import get_graph
from app.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


async def run_agent(
    session_id: str,
    user_message: str,
    websocket: WebSocket,
) -> str:
    """
    Run one turn of the agent for a given session.
    Returns the assistant's text response.
    """
    graph = get_graph()
    config = {"configurable": {"thread_id": session_id}}

    # Check if we have a pending action waiting for confirmation
    state = await graph.aget_state(config)
    pending = state.values.get("pending_action") if state.values else None

    if pending:
        # ── Confirmation turn: handle directly, don't re-enter agent ──────
        confirmed = _parse_confirmation(user_message)

        if confirmed:
            response_text = await _execute_pending(pending)
        else:
            response_text = "No problem, I've cancelled that. Anything else?"

        # Update graph state so the conversation history stays clean
        await graph.aupdate_state(
            config,
            {
                "messages": [
                    HumanMessage(content=user_message),
                    AIMessage(content=response_text),
                ],
                "pending_action": None,
                "confirmed": None,
            },
        )
        return response_text

    # ── Normal turn: run through the full graph ───────────────────────────
    input_state = {
        "messages": [HumanMessage(content=user_message)],
        "pending_action": None,
        "confirmed": None,
    }

    final_state = await graph.ainvoke(input_state, config=config)

    # Extract the last assistant text message
    messages = final_state.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and isinstance(msg.content, str) and msg.content.strip():
            if not hasattr(msg, "tool_calls") or not msg.tool_calls:
                return msg.content

    return "I'm sorry, I didn't quite get that. Could you try again?"


async def _execute_pending(pending: dict) -> str:
    """Execute a confirmed pending tool action directly."""
    tool_name = pending["tool_name"]
    tool_args = pending["args"]

    target_tool = next((t for t in ALL_TOOLS if t.name == tool_name), None)
    if not target_tool:
        return f"Sorry, I couldn't find the tool to execute that action."

    try:
        result = await target_tool.ainvoke(tool_args)
        return f"Done! {result}"
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        return f"Sorry, there was an error: {str(e)}"


def _parse_confirmation(text: str) -> bool:
    """Parse yes/no from user confirmation response."""
    text_lower = text.lower().strip()
    yes_words = {"yes", "yeah", "yep", "yup", "sure", "ok", "okay",
                 "go ahead", "do it", "confirm", "confirmed", "please", "correct"}
    no_words = {"no", "nope", "cancel", "don't", "stop", "never mind",
                "nevermind", "abort", "nah"}

    if any(w in text_lower for w in yes_words):
        return True
    if any(w in text_lower for w in no_words):
        return False
    return True  # default to yes if ambiguous
