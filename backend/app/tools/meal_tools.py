"""Tools for meal planning: generate plans, create calendar events, build grocery lists."""
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from langchain_core.tools import tool
from sqlalchemy import select, delete

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models import (
    MealPlan, Recipe, FamilyMember, FamilyPreference, PantryItem, GroceryItem
)

logger = logging.getLogger(__name__)
TZ = ZoneInfo(settings.app_timezone)


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_calendar_events_for_range(start_date: date, end_date: date) -> list[dict]:
    """Fetch Google Calendar events to detect away / busy days."""
    try:
        from app.integrations.google_calendar import get_calendar_service
        service = await get_calendar_service()

        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=TZ)
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=TZ)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        return events_result.get("items", [])
    except Exception as e:
        logger.warning(f"Could not fetch calendar events: {e}")
        return []


def _detect_away_dates(events: list[dict]) -> set[str]:
    """Return YYYY-MM-DD strings for days that have all-day or travel events."""
    away = set()
    for ev in events:
        summary = (ev.get("summary") or "").lower()
        if any(k in summary for k in ["travel", "away", "vacation", "trip", "flight", "out of town"]):
            start = ev.get("start", {})
            if "date" in start:  # all-day event
                away.add(start["date"])
    return away


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool
async def get_meal_plan(days: int = 7) -> str:
    """
    Get the current meal plan for the next N days.

    Args:
        days: How many days ahead to show (default 7).
    """
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=days)).isoformat()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MealPlan)
            .where(MealPlan.date >= today, MealPlan.date <= end)
            .order_by(MealPlan.date, MealPlan.meal_type)
        )
        plans = result.scalars().all()

    if not plans:
        return f"No meal plan for the next {days} days. Use generate_meal_plan to create one."

    lines = []
    current_date = None
    for p in plans:
        if p.date != current_date:
            current_date = p.date
            lines.append(f"\n{p.date}:")
        lines.append(f"  {p.meal_type}: {p.recipe_name}")
    return "Meal plan:" + "\n".join(lines)


@tool
async def generate_meal_plan(
    days: int = 7,
    start_date: Optional[str] = None,
    overwrite_existing: bool = False,
) -> str:
    """
    Generate a meal plan for the next N days using family preferences, pantry items,
    and calendar (to skip away days). Picks recipes from the database.

    Args:
        days: Number of days to plan (default 7).
        start_date: Start date YYYY-MM-DD (default: today).
        overwrite_existing: If True, replace any existing plan for these dates.
    """
    async with AsyncSessionLocal() as db:
        # Load preferences
        prefs_result = await db.execute(select(FamilyPreference).limit(1))
        prefs = prefs_result.scalar_one_or_none()

        meals_to_plan = json.loads(prefs.meals_to_plan) if prefs else ["dinner"]
        plan_days = min(days, prefs.plan_days_ahead if prefs else 7)
        preferred_cuisines = json.loads(prefs.preferred_cuisines) if prefs else []

        # Load family restrictions
        members_result = await db.execute(select(FamilyMember))
        members = members_result.scalars().all()
        all_restrictions = set()
        for m in members:
            all_restrictions.update(json.loads(m.dietary_restrictions))

        # Load pantry categories for smart picks
        pantry_result = await db.execute(select(PantryItem))
        pantry_items = pantry_result.scalars().all()
        pantry_categories = {p.category for p in pantry_items if p.category}

        # Load recipes
        recipe_result = await db.execute(select(Recipe))
        all_recipes = recipe_result.scalars().all()

        # Filter recipes by dietary restrictions
        def recipe_ok(r: Recipe) -> bool:
            tags = [t.lower() for t in json.loads(r.tags)]
            for restriction in all_restrictions:
                r_lower = restriction.lower()
                if r_lower == "vegetarian" and "vegetarian" not in tags and "vegan" not in tags:
                    # Check ingredients — simple heuristic
                    ings = [i["name"].lower() for i in json.loads(r.ingredients)]
                    meat_keywords = ["chicken", "beef", "pork", "lamb", "shrimp", "bacon", "sausage", "fish", "salmon", "tuna"]
                    if any(mk in " ".join(ings) for mk in meat_keywords):
                        return False
                if r_lower == "vegan" and "vegan" not in tags:
                    return False
                if "nut" in r_lower:
                    ings = [i["name"].lower() for i in json.loads(r.ingredients)]
                    if any("nut" in ing for ing in ings):
                        return False
            return True

        valid_recipes = [r for r in all_recipes if recipe_ok(r)]
        if not valid_recipes:
            valid_recipes = all_recipes  # fallback: ignore restrictions if no recipes pass

        # Date range
        start = date.fromisoformat(start_date) if start_date else date.today()
        end = start + timedelta(days=plan_days - 1)

        # Detect away days from calendar
        calendar_events = await _get_calendar_events_for_range(start, end)
        away_dates = _detect_away_dates(calendar_events)

        # Generate plan
        plan_entries = []
        used_recipe_ids: set[int] = set()

        for day_offset in range(plan_days):
            day = start + timedelta(days=day_offset)
            day_str = day.isoformat()

            if day_str in away_dates:
                continue  # skip away days

            # Check existing entries
            if not overwrite_existing:
                existing_result = await db.execute(
                    select(MealPlan).where(MealPlan.date == day_str)
                )
                existing = existing_result.scalars().all()
                existing_meal_types = {e.meal_type for e in existing}
            else:
                # Delete existing entries for this date
                await db.execute(delete(MealPlan).where(MealPlan.date == day_str))
                existing_meal_types = set()

            for meal_type in meals_to_plan:
                if meal_type in existing_meal_types:
                    continue

                # Pick a recipe: prefer cuisine variety, avoid recent repeats
                candidates = valid_recipes.copy()

                # Prefer preferred cuisines if set
                if preferred_cuisines:
                    cuisine_matches = [r for r in candidates if r.cuisine_type.lower() in [c.lower() for c in preferred_cuisines]]
                    if cuisine_matches:
                        candidates = cuisine_matches

                # Avoid recent repeats
                fresh = [r for r in candidates if r.id not in used_recipe_ids]
                if not fresh:
                    used_recipe_ids.clear()
                    fresh = candidates

                # Pick one (deterministic rotation by day offset)
                idx = (day_offset + len(plan_entries)) % len(fresh)
                chosen = fresh[idx]
                used_recipe_ids.add(chosen.id)

                plan_entries.append(MealPlan(
                    date=day_str,
                    meal_type=meal_type,
                    recipe_id=chosen.id,
                    recipe_name=chosen.name,
                    description=chosen.description,
                    serves=chosen.serves,
                ))

        if not plan_entries:
            return "No new meal plan entries to create (all dates already planned or away)."

        for entry in plan_entries:
            db.add(entry)
        await db.commit()

    lines = [f"  {e.date} {e.meal_type}: {e.recipe_name}" for e in plan_entries]
    return f"Generated {len(plan_entries)} meal plan entries:\n" + "\n".join(lines)


@tool
async def set_meal_plan_entry(
    date_str: str,
    meal_type: str,
    recipe_name: str,
) -> str:
    """
    Manually set or override a single meal plan entry.

    Args:
        date_str: Date in YYYY-MM-DD format.
        meal_type: 'breakfast', 'lunch', or 'dinner'.
        recipe_name: Recipe name (partial match allowed from the recipe database, or any free text).
    """
    async with AsyncSessionLocal() as db:
        # Try to find the recipe
        recipe = None
        result = await db.execute(
            select(Recipe).where(Recipe.name.ilike(f"%{recipe_name}%")).limit(1)
        )
        recipe = result.scalar_one_or_none()

        # Delete existing entry for this date + meal_type
        await db.execute(
            delete(MealPlan).where(
                MealPlan.date == date_str,
                MealPlan.meal_type == meal_type,
            )
        )

        entry = MealPlan(
            date=date_str,
            meal_type=meal_type,
            recipe_id=recipe.id if recipe else None,
            recipe_name=recipe.name if recipe else recipe_name,
            description=recipe.description if recipe else None,
            serves=recipe.serves if recipe else 4,
        )
        db.add(entry)
        await db.commit()

    return f"Set {meal_type} on {date_str} to '{recipe.name if recipe else recipe_name}'."


@tool
async def clear_meal_plan(days: int = 7, start_date: Optional[str] = None) -> str:
    """
    Clear the meal plan for the next N days.

    Args:
        days: How many days to clear (default 7).
        start_date: Start date YYYY-MM-DD (default: today).
    """
    start = date.fromisoformat(start_date) if start_date else date.today()
    end = start + timedelta(days=days)
    start_str = start.isoformat()
    end_str = end.isoformat()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(MealPlan).where(
                MealPlan.date >= start_str,
                MealPlan.date < end_str,
            )
        )
        await db.commit()
        count = result.rowcount

    return f"Cleared {count} meal plan entries from {start_str} to {end_str}."


@tool
async def create_meal_calendar_events(days: int = 7, start_date: Optional[str] = None) -> str:
    """
    Create Google Calendar events for all planned meals in the next N days.
    Uses meal times from family preferences. Only creates events not already synced.

    Args:
        days: How many days of plans to sync (default 7).
        start_date: Start date YYYY-MM-DD (default: today).
    """
    try:
        from app.integrations.google_calendar import get_calendar_service
    except ImportError:
        return "Google Calendar integration not available."

    try:
        service = await get_calendar_service()
    except ValueError:
        return "Google Calendar is not connected. Please connect it first."

    start = date.fromisoformat(start_date) if start_date else date.today()
    end = start + timedelta(days=days)
    start_str = start.isoformat()
    end_str = end.isoformat()

    async with AsyncSessionLocal() as db:
        prefs_result = await db.execute(select(FamilyPreference).limit(1))
        prefs = prefs_result.scalar_one_or_none()

        meal_times = {
            "breakfast": (prefs.breakfast_time if prefs else "08:00"),
            "lunch": (prefs.lunch_time if prefs else "12:00"),
            "dinner": (prefs.dinner_time if prefs else "18:30"),
        }

        plans_result = await db.execute(
            select(MealPlan).where(
                MealPlan.date >= start_str,
                MealPlan.date < end_str,
                MealPlan.calendar_event_id == None,
            ).order_by(MealPlan.date, MealPlan.meal_type)
        )
        plans = plans_result.scalars().all()

        if not plans:
            return "No unsynced meal plan entries found."

        created = 0
        errors = 0
        for plan in plans:
            try:
                meal_time = meal_times.get(plan.meal_type, "18:00")
                hour, minute = map(int, meal_time.split(":"))
                start_dt = datetime(
                    *date.fromisoformat(plan.date).timetuple()[:3],
                    hour, minute, tzinfo=TZ
                )
                end_dt = start_dt + timedelta(hours=1)

                emoji = {"breakfast": "🍳", "lunch": "🥗", "dinner": "🍽"}.get(plan.meal_type, "🍴")
                event_body = {
                    "summary": f"{emoji} {plan.meal_type.capitalize()}: {plan.recipe_name}",
                    "description": plan.description or f"Serves {plan.serves}",
                    "start": {"dateTime": start_dt.isoformat(), "timeZone": settings.app_timezone},
                    "end": {"dateTime": end_dt.isoformat(), "timeZone": settings.app_timezone},
                }
                created_event = service.events().insert(
                    calendarId="primary", body=event_body
                ).execute()
                plan.calendar_event_id = created_event["id"]
                created += 1
            except Exception as e:
                logger.error(f"Failed to create calendar event for {plan.date} {plan.meal_type}: {e}")
                errors += 1

        await db.commit()

    msg = f"Created {created} calendar event{'s' if created != 1 else ''}"
    if errors:
        msg += f" ({errors} failed)"
    return msg + "."


@tool
async def generate_grocery_list_from_plan(days: int = 7, start_date: Optional[str] = None) -> str:
    """
    Generate a grocery list from the meal plan for the next N days.
    Compares recipe ingredients against current pantry and adds only what's missing.

    Args:
        days: How many days of meal plan to scan (default 7).
        start_date: Start date YYYY-MM-DD (default: today).
    """
    start = date.fromisoformat(start_date) if start_date else date.today()
    end = start + timedelta(days=days)
    start_str = start.isoformat()
    end_str = end.isoformat()

    async with AsyncSessionLocal() as db:
        # Get meal plan
        plans_result = await db.execute(
            select(MealPlan).where(
                MealPlan.date >= start_str,
                MealPlan.date < end_str,
            )
        )
        plans = plans_result.scalars().all()

        if not plans:
            return "No meal plan found for this period. Generate a meal plan first."

        # Collect all ingredients needed
        needed: dict[str, list[str]] = {}  # name -> list of quantities
        for plan in plans:
            if plan.recipe_id is None:
                continue
            recipe_result = await db.execute(
                select(Recipe).where(Recipe.id == plan.recipe_id)
            )
            recipe = recipe_result.scalar_one_or_none()
            if recipe is None:
                continue
            for ing in json.loads(recipe.ingredients):
                ing_name = ing["name"].lower()
                qty = f"{ing.get('quantity', '')} {ing.get('unit', '')}".strip()
                if ing_name not in needed:
                    needed[ing_name] = []
                if qty:
                    needed[ing_name].append(qty)

        # Check pantry
        pantry_result = await db.execute(select(PantryItem))
        pantry_items = pantry_result.scalars().all()
        have = {p.name.lower() for p in pantry_items}

        # Add missing items to grocery list
        added = []
        skipped = []
        for ing_name, quantities in needed.items():
            if ing_name in have:
                skipped.append(ing_name)
                continue

            # Check if already on grocery list (unbought)
            existing_result = await db.execute(
                select(GroceryItem).where(
                    GroceryItem.name == ing_name,
                    GroceryItem.bought == False,
                )
            )
            existing = existing_result.scalar_one_or_none()
            if existing:
                skipped.append(ing_name)
                continue

            qty_str = quantities[0] if quantities else None
            grocery = GroceryItem(
                name=ing_name,
                quantity=qty_str,
            )
            db.add(grocery)
            added.append(ing_name)

        await db.commit()

    if not added:
        return f"All ingredients for the {days}-day plan are already in your pantry or grocery list."

    lines = [f"- {name}" for name in sorted(added)]
    result = f"Added {len(added)} item{'s' if len(added) != 1 else ''} to grocery list:\n" + "\n".join(lines)
    if skipped:
        result += f"\n\nAlready have: {', '.join(sorted(skipped))}"
    return result


MEAL_TOOLS = [
    get_meal_plan,
    generate_meal_plan,
    set_meal_plan_entry,
    clear_meal_plan,
    create_meal_calendar_events,
    generate_grocery_list_from_plan,
]
