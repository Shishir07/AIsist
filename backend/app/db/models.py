from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime, Integer, ForeignKey, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ─── Phase 1 ─────────────────────────────────────────────────────────────────

class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    due: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    fire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fired: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GoogleToken(Base):
    __tablename__ = "google_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_uri: Mapped[str] = mapped_column(Text, nullable=False)
    client_id: Mapped[str] = mapped_column(Text, nullable=False)
    client_secret: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── Phase 2 ─────────────────────────────────────────────────────────────────

class IngredientDB(Base):
    """Internal reference database of known ingredients with nutrition info."""
    __tablename__ = "ingredient_db"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    aliases: Mapped[str] = mapped_column(Text, default="[]")          # JSON list
    primary_nutrient: Mapped[str] = mapped_column(String(20), nullable=False)
    # protein | carbs | fat | fiber | vitamins | minerals
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    # protein | vegetable | grain | dairy | condiment | spice | fruit | beverage
    common_units: Mapped[str] = mapped_column(Text, default="[]")     # JSON list
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)   # user-added via voice
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PantryItem(Base):
    __tablename__ = "pantry_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[str] = mapped_column(String(100), nullable=False)  # free text
    ingredient_db_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ingredient_db.id"), nullable=True)
    primary_nutrient: Mapped[str | None] = mapped_column(String(20), nullable=True)  # denormalized
    category: Mapped[str | None] = mapped_column(String(20), nullable=True)          # denormalized
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GroceryItem(Base):
    __tablename__ = "grocery_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ingredient_db_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ingredient_db.id"), nullable=True)
    bought: Mapped[bool] = mapped_column(Boolean, default=False)
    added_to_pantry: Mapped[bool] = mapped_column(Boolean, default=False)
    meal_plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # which plan generated this
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role: Mapped[str] = mapped_column(String(10), default="adult")    # adult | child
    dietary_restrictions: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    likes: Mapped[str] = mapped_column(Text, default="[]")            # JSON list
    dislikes: Mapped[str] = mapped_column(Text, default="[]")         # JSON list
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FamilyPreference(Base):
    """Single row — global meal planning preferences."""
    __tablename__ = "family_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meals_to_plan: Mapped[str] = mapped_column(Text, default='["dinner"]')   # JSON list
    plan_days_ahead: Mapped[int] = mapped_column(Integer, default=7)
    dinner_time: Mapped[str] = mapped_column(String(5), default="18:30")
    lunch_time: Mapped[str] = mapped_column(String(5), default="12:00")
    breakfast_time: Mapped[str] = mapped_column(String(5), default="08:00")
    preferred_cuisines: Mapped[str] = mapped_column(Text, default="[]")      # JSON list
    setup_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── Phase 3 ─────────────────────────────────────────────────────────────────

class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cuisine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    prep_time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    serves: Mapped[int] = mapped_column(Integer, default=4)
    ingredients: Mapped[str] = mapped_column(Text, default="[]")      # JSON [{name, quantity, unit}]
    tags: Mapped[str] = mapped_column(Text, default="[]")             # JSON ["quick","kid-friendly"]
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False)      # YYYY-MM-DD
    meal_type: Mapped[str] = mapped_column(String(10), nullable=False) # breakfast|lunch|dinner
    recipe_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("recipes.id"), nullable=True)
    recipe_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    serves: Mapped[int] = mapped_column(Integer, default=4)
    calendar_event_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
