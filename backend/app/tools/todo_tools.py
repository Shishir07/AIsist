import logging
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy import select, update

from app.db.session import AsyncSessionLocal
from app.db.models import Todo

logger = logging.getLogger(__name__)


@tool
async def add_todo(text: str, priority: str = "medium", due: Optional[str] = None) -> str:
    """
    Add a new todo item.
    Args:
        text: The todo description
        priority: Priority level - 'low', 'medium', or 'high'
        due: Optional due datetime in ISO format
    """
    try:
        async with AsyncSessionLocal() as db:
            todo = Todo(text=text, priority=priority)
            if due:
                from datetime import datetime
                todo.due = datetime.fromisoformat(due)
            db.add(todo)
            await db.commit()
            await db.refresh(todo)
        return f"Todo added: '{text}' (priority: {priority}, id: {todo.id})"
    except Exception as e:
        logger.error(f"add_todo error: {e}")
        return f"Error adding todo: {str(e)}"


@tool
async def list_todos(filter: str = "active") -> str:
    """
    List todo items.
    Args:
        filter: 'active' for incomplete todos, 'all' for everything, 'completed' for done items
    """
    try:
        async with AsyncSessionLocal() as db:
            query = select(Todo).order_by(Todo.created_at.desc())
            if filter == "active":
                query = query.where(Todo.completed == False)
            elif filter == "completed":
                query = query.where(Todo.completed == True)

            result = await db.execute(query)
            todos = result.scalars().all()

        if not todos:
            return "No todos found."

        lines = []
        for t in todos:
            status = "✅" if t.completed else "⬜"
            due_str = f" (due: {t.due.strftime('%b %d %I:%M%p')})" if t.due else ""
            lines.append(f"{status} [{t.id}] [{t.priority.upper()}] {t.text}{due_str}")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"list_todos error: {e}")
        return f"Error listing todos: {str(e)}"


@tool
async def complete_todo(todo_id: int) -> str:
    """
    Mark a todo as completed.
    Args:
        todo_id: The ID of the todo to mark complete
    """
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Todo).where(Todo.id == todo_id))
            todo = result.scalar_one_or_none()
            if not todo:
                return f"Todo with id {todo_id} not found."
            todo.completed = True
            await db.commit()
        return f"Todo #{todo_id} marked as completed ✅"
    except Exception as e:
        logger.error(f"complete_todo error: {e}")
        return f"Error completing todo: {str(e)}"


@tool
async def delete_todo(todo_id: int) -> str:
    """
    Delete a todo item.
    Args:
        todo_id: The ID of the todo to delete
    """
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Todo).where(Todo.id == todo_id))
            todo = result.scalar_one_or_none()
            if not todo:
                return f"Todo with id {todo_id} not found."
            await db.delete(todo)
            await db.commit()
        return f"Todo #{todo_id} deleted."
    except Exception as e:
        logger.error(f"delete_todo error: {e}")
        return f"Error deleting todo: {str(e)}"


TODO_TOOLS = [add_todo, list_todos, complete_todo, delete_todo]
