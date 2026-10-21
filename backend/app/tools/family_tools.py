"""Tools for managing family members and meal preferences."""
import json
import logging
from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import FamilyMember, FamilyPreference

logger = logging.getLogger(__name__)


@tool
async def get_family_profile() -> str:
    """Get the full family profile: all members and meal planning preferences."""
    async with AsyncSessionLocal() as db:
        members_result = await db.execute(select(FamilyMember).order_by(FamilyMember.id))
        members = members_result.scalars().all()

        prefs_result = await db.execute(select(FamilyPreference).limit(1))
        prefs = prefs_result.scalar_one_or_none()

    if not members and not prefs:
        return "No family profile set up yet."

    parts = []
    if members:
        member_lines = []
        for m in members:
            restrictions = json.loads(m.dietary_restrictions)
            likes = json.loads(m.likes)
            dislikes = json.loads(m.dislikes)
            line = f"- {m.name} ({m.role}"
            if m.age:
                line += f", age {m.age}"
            line += ")"
            if restrictions:
                line += f": restrictions={restrictions}"
            if likes:
                line += f", likes={likes}"
            if dislikes:
                line += f", dislikes={dislikes}"
            member_lines.append(line)
        parts.append("Family members:\n" + "\n".join(member_lines))

    if prefs:
        meals = json.loads(prefs.meals_to_plan)
        cuisines = json.loads(prefs.preferred_cuisines)
        parts.append(
            f"Meal preferences: plan {meals} for {prefs.plan_days_ahead} days ahead. "
            f"Times: breakfast {prefs.breakfast_time}, lunch {prefs.lunch_time}, dinner {prefs.dinner_time}. "
            f"Preferred cuisines: {cuisines if cuisines else 'any'}. "
            f"Setup complete: {prefs.setup_complete}."
        )

    return "\n\n".join(parts)


@tool
async def upsert_family_member(
    name: str,
    role: str = "adult",
    age: Optional[int] = None,
    dietary_restrictions: Optional[list[str]] = None,
    likes: Optional[list[str]] = None,
    dislikes: Optional[list[str]] = None,
) -> str:
    """
    Add or update a family member. If a member with the same name exists, update them.

    Args:
        name: Member's name.
        role: 'adult' or 'child'.
        age: Optional age.
        dietary_restrictions: e.g. ['vegetarian', 'nut allergy'].
        likes: Foods they enjoy, e.g. ['pasta', 'chicken'].
        dislikes: Foods they dislike, e.g. ['mushrooms', 'broccoli'].
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.name == name)
        )
        member = result.scalar_one_or_none()

        if member is None:
            member = FamilyMember(name=name)
            db.add(member)

        member.role = role
        if age is not None:
            member.age = age
        if dietary_restrictions is not None:
            member.dietary_restrictions = json.dumps(dietary_restrictions)
        if likes is not None:
            member.likes = json.dumps(likes)
        if dislikes is not None:
            member.dislikes = json.dumps(dislikes)

        await db.commit()

    return f"Family member '{name}' saved."


@tool
async def remove_family_member(name: str) -> str:
    """Remove a family member by name."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.name == name)
        )
        member = result.scalar_one_or_none()
        if member is None:
            return f"No family member named '{name}' found."
        await db.delete(member)
        await db.commit()
    return f"Removed {name} from the family profile."


@tool
async def update_meal_preferences(
    meals_to_plan: Optional[list[str]] = None,
    plan_days_ahead: Optional[int] = None,
    dinner_time: Optional[str] = None,
    lunch_time: Optional[str] = None,
    breakfast_time: Optional[str] = None,
    preferred_cuisines: Optional[list[str]] = None,
    setup_complete: Optional[bool] = None,
) -> str:
    """
    Update global meal planning preferences (single-row table).

    Args:
        meals_to_plan: Which meals to plan, e.g. ['breakfast', 'dinner'].
        plan_days_ahead: How many days ahead to plan (e.g. 7).
        dinner_time: Time string HH:MM e.g. '18:30'.
        lunch_time: Time string HH:MM e.g. '12:00'.
        breakfast_time: Time string HH:MM e.g. '08:00'.
        preferred_cuisines: e.g. ['Italian', 'Mexican', 'Asian'].
        setup_complete: Set True when family setup wizard is finished.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(FamilyPreference).limit(1))
        prefs = result.scalar_one_or_none()

        if prefs is None:
            prefs = FamilyPreference()
            db.add(prefs)

        if meals_to_plan is not None:
            prefs.meals_to_plan = json.dumps(meals_to_plan)
        if plan_days_ahead is not None:
            prefs.plan_days_ahead = plan_days_ahead
        if dinner_time is not None:
            prefs.dinner_time = dinner_time
        if lunch_time is not None:
            prefs.lunch_time = lunch_time
        if breakfast_time is not None:
            prefs.breakfast_time = breakfast_time
        if preferred_cuisines is not None:
            prefs.preferred_cuisines = json.dumps(preferred_cuisines)
        if setup_complete is not None:
            prefs.setup_complete = setup_complete

        await db.commit()

    return "Meal preferences updated."


FAMILY_TOOLS = [
    get_family_profile,
    upsert_family_member,
    remove_family_member,
    update_meal_preferences,
]
