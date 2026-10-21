"""Tools for searching and managing recipes."""
import json
import logging
from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import select, or_
from app.db.session import AsyncSessionLocal
from app.db.models import Recipe

logger = logging.getLogger(__name__)


@tool
async def search_recipes(
    query: Optional[str] = None,
    cuisine_type: Optional[str] = None,
    tag: Optional[str] = None,
    max_prep_minutes: Optional[int] = None,
) -> str:
    """
    Search the recipe database. Returns matching recipes with brief details.

    Args:
        query: Free-text search in recipe name or description.
        cuisine_type: Filter by cuisine, e.g. 'Italian', 'Mexican', 'Asian', 'Mediterranean', 'Indian', 'North American'.
        tag: Filter by tag, e.g. 'quick', 'kid-friendly', 'vegetarian', 'high-protein'.
        max_prep_minutes: Only return recipes that take at most this many minutes.
    """
    async with AsyncSessionLocal() as db:
        stmt = select(Recipe)
        if cuisine_type:
            stmt = stmt.where(Recipe.cuisine_type.ilike(f"%{cuisine_type}%"))
        if max_prep_minutes:
            stmt = stmt.where(Recipe.prep_time_minutes <= max_prep_minutes)
        result = await db.execute(stmt)
        recipes = result.scalars().all()

    # In-memory filter for query and tag (JSON fields)
    if query:
        q = query.lower()
        recipes = [r for r in recipes if q in r.name.lower() or (r.description and q in r.description.lower())]
    if tag:
        t = tag.lower()
        recipes = [r for r in recipes if t in [x.lower() for x in json.loads(r.tags)]]

    if not recipes:
        return "No recipes found matching those criteria."

    lines = []
    for r in recipes:
        tags = json.loads(r.tags)
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"- {r.name} ({r.cuisine_type}, {r.prep_time_minutes} min, serves {r.serves}){tag_str}")
    return f"Found {len(recipes)} recipe(s):\n" + "\n".join(lines)


@tool
async def get_recipe_details(name: str) -> str:
    """
    Get full details for a recipe including ingredients and instructions.

    Args:
        name: Recipe name (partial match allowed).
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Recipe).where(Recipe.name.ilike(f"%{name}%")).limit(1)
        )
        recipe = result.scalar_one_or_none()

    if recipe is None:
        return f"No recipe found matching '{name}'."

    ingredients = json.loads(recipe.ingredients)
    tags = json.loads(recipe.tags)
    ing_lines = [f"  • {i.get('quantity', '')} {i.get('unit', '')} {i['name']}".strip() for i in ingredients]
    return (
        f"{recipe.name} ({recipe.cuisine_type})\n"
        f"Prep: {recipe.prep_time_minutes} min | Serves: {recipe.serves}\n"
        f"Tags: {', '.join(tags) if tags else 'none'}\n"
        f"Description: {recipe.description or 'N/A'}\n"
        f"Ingredients:\n" + "\n".join(ing_lines) + "\n"
        f"Instructions: {recipe.instructions or 'N/A'}"
    )


@tool
async def add_recipe(
    name: str,
    cuisine_type: str,
    prep_time_minutes: int,
    serves: int,
    ingredients: list[dict],
    description: Optional[str] = None,
    instructions: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> str:
    """
    Add a new custom recipe to the database.

    Args:
        name: Recipe name.
        cuisine_type: e.g. 'Italian', 'Asian', 'Mexican'.
        prep_time_minutes: Total prep + cook time in minutes.
        serves: Number of servings.
        ingredients: List of dicts with keys: name, quantity (optional), unit (optional).
                     Example: [{"name": "chicken breast", "quantity": "500", "unit": "grams"}]
        description: Short description.
        instructions: Cooking instructions.
        tags: Tags like ['quick', 'kid-friendly', 'vegetarian', 'high-protein'].
    """
    async with AsyncSessionLocal() as db:
        # Check for duplicate name
        result = await db.execute(
            select(Recipe).where(Recipe.name.ilike(name))
        )
        existing = result.scalar_one_or_none()
        if existing:
            return f"A recipe named '{name}' already exists."

        recipe = Recipe(
            name=name,
            cuisine_type=cuisine_type,
            prep_time_minutes=prep_time_minutes,
            serves=serves,
            ingredients=json.dumps(ingredients),
            description=description,
            instructions=instructions,
            tags=json.dumps(tags or []),
            is_builtin=False,
        )
        db.add(recipe)
        await db.commit()

    return f"Recipe '{name}' added ({cuisine_type}, {prep_time_minutes} min, serves {serves})."


RECIPE_TOOLS = [
    search_recipes,
    get_recipe_details,
    add_recipe,
]
