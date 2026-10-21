import logging
from datetime import datetime

from langchain_core.tools import tool
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models import Reminder

logger = logging.getLogger(__name__)


@tool
async def set_reminder(text: str, fire_at_iso: str) -> str:
    """
    Set a reminder that will fire at a specific time.
    Args:
        text: What to remind the user about
        fire_at_iso: When to fire the reminder in ISO format e.g. 2024-01-15T15:00:00
    """
    try:
        fire_at = datetime.fromisoformat(fire_at_iso)
        async with AsyncSessionLocal() as db:
            reminder = Reminder(text=text, fire_at=fire_at)
            db.add(reminder)
            await db.commit()
            await db.refresh(reminder)

        return (
            f"Reminder set: '{text}' at {fire_at.strftime('%I:%M %p on %B %d')} "
            f"(id: {reminder.id})"
        )
    except Exception as e:
        logger.error(f"set_reminder error: {e}")
        return f"Error setting reminder: {str(e)}"


@tool
async def list_reminders() -> str:
    """List all upcoming (unfired) reminders."""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Reminder)
                .where(Reminder.fired == False)
                .order_by(Reminder.fire_at)
            )
            reminders = result.scalars().all()

        if not reminders:
            return "No upcoming reminders."

        lines = []
        for r in reminders:
            lines.append(
                f"[{r.id}] '{r.text}' at {r.fire_at.strftime('%I:%M %p on %B %d')}"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"list_reminders error: {e}")
        return f"Error listing reminders: {str(e)}"


@tool
async def cancel_reminder(reminder_id: int) -> str:
    """
    Cancel an upcoming reminder.
    Args:
        reminder_id: The ID of the reminder to cancel
    """
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Reminder).where(Reminder.id == reminder_id)
            )
            reminder = result.scalar_one_or_none()
            if not reminder:
                return f"Reminder with id {reminder_id} not found."
            await db.delete(reminder)
            await db.commit()
        return f"Reminder #{reminder_id} cancelled."
    except Exception as e:
        logger.error(f"cancel_reminder error: {e}")
        return f"Error cancelling reminder: {str(e)}"


REMINDER_TOOLS = [set_reminder, list_reminders, cancel_reminder]
