"""Tools for managing the grocery list."""
import logging
from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import select, delete
from app.db.session import AsyncSessionLocal
from app.db.models import GroceryItem, PantryItem

logger = logging.getLogger(__name__)


@tool
async def add_grocery_item(name: str, quantity: Optional[str] = None) -> str:
    """
    Add an item to the grocery list.

    Args:
        name: Item name, e.g. 'milk', 'chicken breast'.
        quantity: Optional quantity, e.g. '2 liters', '500 grams'.
    """
    async with AsyncSessionLocal() as db:
        # Check if already on the list (unbought)
        result = await db.execute(
            select(GroceryItem).where(
                GroceryItem.name == name.lower(),
                GroceryItem.bought == False,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            if quantity:
                existing.quantity = quantity
            await db.commit()
            return f"'{name}' is already on the grocery list{f' — updated to {quantity}' if quantity else ''}."

        item = GroceryItem(
            name=name.lower(),
            quantity=quantity,
        )
        db.add(item)
        await db.commit()

    return f"Added '{name}'{f' ({quantity})' if quantity else ''} to the grocery list."


@tool
async def list_grocery_items(show_bought: bool = False) -> str:
    """
    List grocery items.

    Args:
        show_bought: If True, include already-bought items too. Default False.
    """
    async with AsyncSessionLocal() as db:
        query = select(GroceryItem).order_by(GroceryItem.name)
        if not show_bought:
            query = query.where(GroceryItem.bought == False)
        result = await db.execute(query)
        items = result.scalars().all()

    if not items:
        return "Grocery list is empty." if not show_bought else "No grocery items found."

    lines = []
    for i in items:
        qty = f" ({i.quantity})" if i.quantity else ""
        status = " ✓" if i.bought else ""
        lines.append(f"- {i.name}{qty}{status}")
    return "Grocery list:\n" + "\n".join(lines)


@tool
async def mark_grocery_bought(name: str) -> str:
    """
    Mark a grocery item as bought.

    Args:
        name: Item name.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(GroceryItem).where(
                GroceryItem.name == name.lower(),
                GroceryItem.bought == False,
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            return f"'{name}' not found on the grocery list."
        item.bought = True
        await db.commit()
    return f"Marked '{name}' as bought."


@tool
async def move_grocery_to_pantry(name: str, quantity: Optional[str] = None) -> str:
    """
    Move a bought grocery item to the pantry. Marks it as added_to_pantry and creates/updates pantry entry.

    Args:
        name: Grocery item name.
        quantity: Quantity to add to pantry. If omitted, uses the grocery item's quantity.
    """
    async with AsyncSessionLocal() as db:
        # Find grocery item (bought or not)
        result = await db.execute(
            select(GroceryItem).where(GroceryItem.name == name.lower())
        )
        grocery = result.scalar_one_or_none()
        if grocery is None:
            return f"'{name}' not found in grocery list."

        grocery.bought = True
        grocery.added_to_pantry = True

        # Upsert pantry
        pantry_result = await db.execute(
            select(PantryItem).where(PantryItem.name == name.lower())
        )
        pantry_item = pantry_result.scalar_one_or_none()
        qty = quantity or grocery.quantity or "some"

        if pantry_item:
            pantry_item.quantity = qty
        else:
            pantry_item = PantryItem(
                name=name.lower(),
                quantity=qty,
                ingredient_db_id=grocery.ingredient_db_id,
            )
            db.add(pantry_item)

        await db.commit()
    return f"Moved '{name}' to pantry ({qty})."


@tool
async def clear_bought_grocery_items() -> str:
    """Remove all bought grocery items from the list (cleanup)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(GroceryItem).where(GroceryItem.bought == True)
        )
        items = result.scalars().all()
        count = len(items)
        for item in items:
            await db.delete(item)
        await db.commit()
    if count == 0:
        return "No bought items to clear."
    return f"Cleared {count} bought item{'s' if count != 1 else ''} from the grocery list."


@tool
async def remove_grocery_item(name: str) -> str:
    """
    Remove an item from the grocery list entirely.

    Args:
        name: Item name.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(GroceryItem).where(GroceryItem.name == name.lower())
        )
        item = result.scalar_one_or_none()
        if item is None:
            return f"'{name}' not found in grocery list."
        await db.delete(item)
        await db.commit()
    return f"Removed '{name}' from grocery list."


GROCERY_TOOLS = [
    add_grocery_item,
    list_grocery_items,
    mark_grocery_bought,
    move_grocery_to_pantry,
    clear_bought_grocery_items,
    remove_grocery_item,
]
