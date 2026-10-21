from typing import Annotated, Optional
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Full conversation history (auto-merged by LangGraph)
    messages: Annotated[list, add_messages]

    # When agent wants to call a write tool, it stores the intent here
    # and waits for user confirmation before executing
    pending_action: Optional[dict]  # {"tool": "create_event", "args": {...}, "summary": "..."}

    # Set to True when user says "yes/confirm", False for "no/cancel"
    confirmed: Optional[bool]
