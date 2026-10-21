from contextlib import AsyncExitStack

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.agent.state import AgentState
from app.agent.nodes import (
    agent_node,
    confirm_node,
    execute_confirmed_node,
    cancel_node,
    tool_node,
    should_confirm,
    after_confirm,
)
from app.config import settings

_compiled_graph = None
_exit_stack = AsyncExitStack()


def build_graph(checkpointer: AsyncPostgresSaver) -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("confirm", confirm_node)
    graph.add_node("execute", execute_confirmed_node)
    graph.add_node("cancel", cancel_node)

    graph.add_edge(START, "agent")

    graph.add_conditional_edges(
        "agent",
        should_confirm,
        {"confirm": "confirm", "tools": "tools", "end": END},
    )

    graph.add_edge("tools", "agent")

    graph.add_conditional_edges(
        "confirm",
        after_confirm,
        {"execute": "execute", "cancel": "cancel", "wait": END},
    )

    graph.add_edge("execute", END)
    graph.add_edge("cancel", END)

    return graph.compile(checkpointer=checkpointer)


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        raise RuntimeError("Graph not initialized. Call init_graph() first.")
    return _compiled_graph


async def init_graph():
    """Initialize the LangGraph agent with Postgres checkpointing."""
    global _compiled_graph

    # Strip +asyncpg for psycopg3 (langgraph-checkpoint-postgres uses psycopg3)
    db_uri = settings.database_url.replace("postgresql+asyncpg", "postgresql")

    checkpointer = await _exit_stack.enter_async_context(
        AsyncPostgresSaver.from_conn_string(db_uri)
    )
    await checkpointer.setup()
    _compiled_graph = build_graph(checkpointer)


async def close_graph():
    """Call on app shutdown."""
    await _exit_stack.aclose()
