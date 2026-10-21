"""Tools for managing the pantry inventory."""
import json
import logging
from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.db.models import PantryItem, IngredientDB

logger = logging.getLogger(__name__)


async def _resolve_ingredient(db, name: str) -> tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Try to match name against IngredientDB (by name or alias).
    Returns (ingredient_db_id, primary_nutrient, category) or (None, None, None).
    """
    name_lower = name.strip().lower()

    # Exact name match
    result = await db.execute(
        select(IngredientDB).where(IngredientDB.name == name_lower)
    )
    ing = result.scalar_one_or_none()
    if ing:
        return ing.id, ing.primary_nutrient, ing.category

    # Alias search
    all_ings = (await db.execute(select(IngredientDB))).scalars().all()
    for ing in all_ings:
        aliases = json.loads(ing.aliases)
        if name_lower in [a.lower() for a in aliases]:
            return ing.id, ing.primary_nutrient, ing.category

    return None, None, None


@tool
async def add_pantry_item(
    name: str,
    quantity: str,
    primary_nutrient: Optional[str] = None,
) -> str:
    """
    Add or update an item in the pantry.

    If the ingredient is unknown (not in the internal database), it will still be added.
    Use primary_nutrient to manually classify unknown ingredients:
    protein | carbs | fat | fiber | vitamins | minerals.

    Args:
        name: Ingredient name, e.g. 'chicken breast', 'rice', 'broccoli'.
        quantity: Free-text quantity, e.g. '500 grams', '2 cans', '1 bunch'.
        primary_nutrient: Optional manual classification for unknown ingredients.
    """
    async with AsyncSessionLocal() as db:
        db_id, db_nutrient, db_category = await _resolve_ingredient(db, name)

        # Existing item? Update quantity
        result = await db.execute(
            select(PantryItem).where(PantryItem.name == name.lower())
        )
        item = result.scalar_one_or_none()

        if item is None:
            item = PantryItem(name=name.lower())
            db.add(item)

        item.quantity = quantity
        item.ingredient_db_id = db_id
        item.primary_nutrient = db_nutrient or primary_nutrient
        item.category = db_category

        await db.commit()

    known = "✓" if db_id else "⚠ not in ingredient DB"
    return f"Pantry: '{name}' — {quantity} ({known})."


@tool
async def list_pantry_items(category: Optional[str] = None) -> str:
    """
    List all pantry items, optionally filtered by category.

    Args:
        category: Optional filter: protein | grain | vegetable | fruit | dairy | condiment | spice | beverage
    """
    async with AsyncSessionLocal() as db:
        query = select(PantryItem).order_by(PantryItem.name)
        if category:
            query = query.where(PantryItem.category == category)
        result = await db.execute(query)
        items = result.scalars().all()

    if not items:
        return "Pantry is empty." if not category else f"No {category} items in pantry."

    lines = [f"- {i.name}: {i.quantity}" for i in items]
    return "Pantry:\n" + "\n".join(lines)


@tool
async def update_pantry_item(name: str, quantity: str) -> str:
    """
    Update the quantity of an existing pantry item.

    Args:
        name: Item name.
        quantity: New quantity, e.g. '3 cans', '250 grams'.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PantryItem).where(PantryItem.name == name.lower())
        )
        item = result.scalar_one_or_none()
        if item is None:
            return f"'{name}' not found in pantry. Use add_pantry_item to add it."
        item.quantity = quantity
        await db.commit()
    return f"Updated '{name}' to {quantity}."


@tool
async def remove_pantry_item(name: str) -> str:
    """
    Remove an item from the pantry entirely.

    Args:
        name: Item name to remove.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PantryItem).where(PantryItem.name == name.lower())
        )
        item = result.scalar_one_or_none()
        if item is None:
            return f"'{name}' not found in pantry."
        await db.delete(item)
        await db.commit()
    return f"Removed '{name}' from pantry."


@tool
async def classify_unknown_ingredient(
    name: str,
    primary_nutrient: str,
    category: str,
) -> str:
    """
    Add a new ingredient to the internal IngredientDB after the user identifies its type.
    Call this after asking the user 'Is X a protein, carb, vegetable, etc.?'

    Args:
        name: Ingredient name.
        primary_nutrient: One of: protein | carbs | fat | fiber | vitamins | minerals
        category: One of: protein | grain | vegetable | fruit | dairy | condiment | spice | beverage
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(IngredientDB).where(IngredientDB.name == name.lower())
        )
        existing = result.scalar_one_or_none()
        if existing:
            return f"'{name}' is already in the ingredient database."

        new_ing = IngredientDB(
            name=name.lower(),
            aliases=json.dumps([]),
            primary_nutrient=primary_nutrient,
            category=category,
            common_units=json.dumps([]),
            is_custom=True,
        )
        db.add(new_ing)
        await db.commit()

        # Now update any pantry items with this name
        result2 = await db.execute(
            select(PantryItem).where(PantryItem.name == name.lower())
        )
        items = result2.scalars().all()
        for item in items:
            item.primary_nutrient = primary_nutrient
            item.category = category
            item.ingredient_db_id = new_ing.id
        await db.commit()

    return f"Added '{name}' to ingredient database as {category} ({primary_nutrient})."


PANTRY_TOOLS = [
    add_pantry_item,
    list_pantry_items,
    update_pantry_item,
    remove_pantry_item,
    classify_unknown_ingredient,
]
