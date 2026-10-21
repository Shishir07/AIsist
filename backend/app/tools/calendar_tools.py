import logging
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from app.integrations.google_calendar import get_calendar_service
from app.config import settings

logger = logging.getLogger(__name__)
TZ = ZoneInfo(settings.app_timezone)


def _to_rfc3339(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.isoformat()


@tool
async def list_events(start_iso: str, end_iso: str, calendar_id: str = "primary") -> str:
    """
    List calendar events between two ISO datetime strings.
    Use this when the user asks what's on their calendar, schedule, or agenda.
    Args:
        start_iso: Start datetime in ISO format e.g. 2024-01-15T00:00:00
        end_iso: End datetime in ISO format e.g. 2024-01-15T23:59:59
        calendar_id: Calendar ID, defaults to 'primary'
    """
    try:
        service = await get_calendar_service()
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=_to_rfc3339(start_dt),
            timeMax=_to_rfc3339(end_dt),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = result.get("items", [])
        if not events:
            return "No events found in that time range."

        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", ""))
            title = e.get("summary", "Untitled")
            attendees = [a["email"] for a in e.get("attendees", [])]
            line = f"- {title} at {start}"
            if attendees:
                line += f" (with {', '.join(attendees)})"
            lines.append(line)

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"list_events error: {e}")
        return f"Error fetching events: {str(e)}"


@tool
async def find_free_slot(
    duration_minutes: int,
    search_start_iso: str,
    search_end_iso: str,
    calendar_id: str = "primary",
) -> str:
    """
    Find the first available free slot of the given duration within a time window.
    Use this when the user wants to find a free slot or schedule a meeting.
    Args:
        duration_minutes: How long the slot needs to be in minutes
        search_start_iso: Start of search window ISO datetime
        search_end_iso: End of search window ISO datetime
        calendar_id: Calendar ID, defaults to 'primary'
    """
    try:
        service = await get_calendar_service()
        search_start_dt = datetime.fromisoformat(search_start_iso)
        search_end_dt = datetime.fromisoformat(search_end_iso)
        result = service.events().list(
            calendarId=calendar_id,
            timeMin=_to_rfc3339(search_start_dt),
            timeMax=_to_rfc3339(search_end_dt),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = result.get("items", [])
        busy_slots = []
        for e in events:
            s = e["start"].get("dateTime")
            en = e["end"].get("dateTime")
            if s and en:
                busy_slots.append((datetime.fromisoformat(s), datetime.fromisoformat(en)))

        # Walk the window to find a free slot
        window_start = datetime.fromisoformat(search_start_iso)
        window_end = datetime.fromisoformat(search_end_iso)
        cursor = window_start

        for busy_start, busy_end in sorted(busy_slots):
            if cursor + timedelta(minutes=duration_minutes) <= busy_start:
                slot_end = cursor + timedelta(minutes=duration_minutes)
                return (
                    f"Free slot found: {cursor.strftime('%I:%M %p')} to "
                    f"{slot_end.strftime('%I:%M %p')} on {cursor.strftime('%A, %B %d')}"
                )
            cursor = max(cursor, busy_end)

        if cursor + timedelta(minutes=duration_minutes) <= window_end:
            slot_end = cursor + timedelta(minutes=duration_minutes)
            return (
                f"Free slot found: {cursor.strftime('%I:%M %p')} to "
                f"{slot_end.strftime('%I:%M %p')} on {cursor.strftime('%A, %B %d')}"
            )

        return "No free slot found in that window. Try a different time range."
    except Exception as e:
        logger.error(f"find_free_slot error: {e}")
        return f"Error finding free slot: {str(e)}"


@tool
async def create_event(
    title: str,
    start_iso: str,
    end_iso: str,
    description: Optional[str] = None,
    attendee_emails: Optional[list[str]] = None,
    calendar_id: str = "primary",
) -> str:
    """
    Create a calendar event. ALWAYS confirm with user before calling this.
    Args:
        title: Event title/summary
        start_iso: Start datetime ISO format
        end_iso: End datetime ISO format
        description: Optional event description
        attendee_emails: Optional list of attendee email addresses
        calendar_id: Calendar ID, defaults to 'primary'
    """
    try:
        service = await get_calendar_service()
        start_rfc = _to_rfc3339(datetime.fromisoformat(start_iso))
        end_rfc = _to_rfc3339(datetime.fromisoformat(end_iso))
        body = {
            "summary": title,
            "start": {"dateTime": start_rfc, "timeZone": settings.app_timezone},
            "end": {"dateTime": end_rfc, "timeZone": settings.app_timezone},
        }
        if description:
            body["description"] = description
        if attendee_emails:
            body["attendees"] = [{"email": e} for e in attendee_emails]
            body["sendUpdates"] = "all"  # sends invite emails

        event = service.events().insert(calendarId=calendar_id, body=body).execute()
        return f"Event created: '{title}' from {start_iso} to {end_iso}. Event ID: {event['id']}"
    except Exception as e:
        logger.error(f"create_event error: {e}")
        return f"Error creating event: {str(e)}"


@tool
async def update_event(
    event_id: str,
    title: Optional[str] = None,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
    description: Optional[str] = None,
    calendar_id: str = "primary",
) -> str:
    """
    Update an existing calendar event. ALWAYS confirm with user before calling this.
    Args:
        event_id: The Google Calendar event ID
        title: New title (optional)
        start_iso: New start datetime ISO (optional)
        end_iso: New end datetime ISO (optional)
        description: New description (optional)
        calendar_id: Calendar ID, defaults to 'primary'
    """
    try:
        service = await get_calendar_service()
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        if title:
            event["summary"] = title
        if start_iso:
            event["start"] = {"dateTime": start_iso, "timeZone": settings.app_timezone}
        if end_iso:
            event["end"] = {"dateTime": end_iso, "timeZone": settings.app_timezone}
        if description:
            event["description"] = description

        updated = service.events().update(
            calendarId=calendar_id, eventId=event_id, body=event
        ).execute()
        return f"Event updated successfully: '{updated.get('summary')}'"
    except Exception as e:
        logger.error(f"update_event error: {e}")
        return f"Error updating event: {str(e)}"


@tool
async def delete_event(event_id: str, calendar_id: str = "primary") -> str:
    """
    Delete a calendar event. ALWAYS confirm with user before calling this.
    Args:
        event_id: The Google Calendar event ID
        calendar_id: Calendar ID, defaults to 'primary'
    """
    try:
        service = await get_calendar_service()
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return f"Event {event_id} deleted successfully."
    except Exception as e:
        logger.error(f"delete_event error: {e}")
        return f"Error deleting event: {str(e)}"


# Export all calendar tools
CALENDAR_TOOLS = [list_events, find_free_slot, create_event, update_event, delete_event]
