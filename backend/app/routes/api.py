import json
from datetime import date, timedelta

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.integrations.google_calendar import router as google_auth_router
from app.db.session import AsyncSessionLocal
from app.db.models import (
    GoogleToken, FamilyMember, FamilyPreference,
    PantryItem, GroceryItem, MealPlan,
)

router = APIRouter()

# Google OAuth routes
router.include_router(google_auth_router, prefix="/auth", tags=["auth"])


@router.delete("/auth/google/disconnect")
async def google_disconnect():
    """Remove stored Google token — forces re-auth."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(GoogleToken))
        tokens = result.scalars().all()
        for token in tokens:
            await db.delete(token)
        await db.commit()
    return {"status": "Google Calendar disconnected"}


@router.get("/status")
async def get_status():
    """Return connection status for frontend."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(GoogleToken).limit(1))
        token = result.scalar_one_or_none()

    return {
        "google_calendar_connected": token is not None,
        "google_login_url": "/api/auth/google/login",
    }


@router.get("/session/history")
async def get_session_history():
    """Return recent conversation history - placeholder for Phase 1."""
    return {"messages": []}


@router.get("/todos")
async def get_todos():
    """List todos - full implementation via agent tools."""
    return {"todos": []}


# ─── Phase 2+3 read endpoints ────────────────────────────────────────────────

@router.get("/family")
async def get_family():
    """Return family members and meal preferences."""
    async with AsyncSessionLocal() as db:
        members_result = await db.execute(
            select(FamilyMember).order_by(FamilyMember.id)
        )
        members = members_result.scalars().all()

        prefs_result = await db.execute(select(FamilyPreference).limit(1))
        prefs = prefs_result.scalar_one_or_none()

    return {
        "members": [
            {
                "id": m.id,
                "name": m.name,
                "role": m.role,
                "age": m.age,
                "dietary_restrictions": json.loads(m.dietary_restrictions),
                "likes": json.loads(m.likes),
                "dislikes": json.loads(m.dislikes),
            }
            for m in members
        ],
        "prefs": {
            "meals_to_plan": json.loads(prefs.meals_to_plan),
            "plan_days_ahead": prefs.plan_days_ahead,
            "dinner_time": prefs.dinner_time,
            "lunch_time": prefs.lunch_time,
            "breakfast_time": prefs.breakfast_time,
            "preferred_cuisines": json.loads(prefs.preferred_cuisines),
            "setup_complete": prefs.setup_complete,
        } if prefs else None,
    }


@router.get("/pantry")
async def get_pantry():
    """Return all pantry items."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PantryItem).order_by(PantryItem.name)
        )
        items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "name": i.name,
                "quantity": i.quantity,
                "category": i.category,
                "primary_nutrient": i.primary_nutrient,
                "updated_at": i.updated_at.isoformat(),
            }
            for i in items
        ]
    }


@router.get("/grocery")
async def get_grocery():
    """Return all grocery items (unbought first)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(GroceryItem).order_by(GroceryItem.bought, GroceryItem.name)
        )
        items = result.scalars().all()

    return {
        "items": [
            {
                "id": i.id,
                "name": i.name,
                "quantity": i.quantity,
                "bought": i.bought,
            }
            for i in items
        ]
    }


@router.patch("/grocery/{item_id}/bought")
async def mark_grocery_bought_api(item_id: int):
    """Mark a grocery item as bought from the UI."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(GroceryItem).where(GroceryItem.id == item_id))
        item = result.scalar_one_or_none()
        if item is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Item not found")
        item.bought = True
        await db.commit()
    return {"status": "ok"}


@router.get("/meal-plan")
async def get_meal_plan(days: int = 7):
    """Return meal plan for the next N days."""
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=days)).isoformat()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MealPlan)
            .where(MealPlan.date >= today, MealPlan.date <= end)
            .order_by(MealPlan.date, MealPlan.meal_type)
        )
        plans = result.scalars().all()

    return {
        "entries": [
            {
                "id": p.id,
                "date": p.date,
                "meal_type": p.meal_type,
                "recipe_name": p.recipe_name,
                "description": p.description,
                "serves": p.serves,
                "calendar_event_id": p.calendar_event_id,
            }
            for p in plans
        ]
    }
