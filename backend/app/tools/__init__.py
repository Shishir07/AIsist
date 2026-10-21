from app.tools.calendar_tools import CALENDAR_TOOLS
from app.tools.todo_tools import TODO_TOOLS
from app.tools.reminder_tools import REMINDER_TOOLS
from app.tools.family_tools import FAMILY_TOOLS
from app.tools.pantry_tools import PANTRY_TOOLS
from app.tools.grocery_tools import GROCERY_TOOLS
from app.tools.recipe_tools import RECIPE_TOOLS
from app.tools.meal_tools import MEAL_TOOLS

ALL_TOOLS = (
    CALENDAR_TOOLS
    + TODO_TOOLS
    + REMINDER_TOOLS
    + FAMILY_TOOLS
    + PANTRY_TOOLS
    + GROCERY_TOOLS
    + RECIPE_TOOLS
    + MEAL_TOOLS
)

# Write tools require confirmation before execution
WRITE_TOOL_NAMES = {
    "create_event",
    "update_event",
    "delete_event",
    "create_meal_calendar_events",
}
