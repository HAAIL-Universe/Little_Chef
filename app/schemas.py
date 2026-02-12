from __future__ import annotations

from pydantic import BaseModel, Field, conlist
from typing import Optional, Dict, Any, List, Literal, Union
from enum import Enum


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-friendly message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra error metadata")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status indicator", pattern="^ok$")


class UserMe(BaseModel):
    user_id: str
    provider_subject: Optional[str] = None
    email: Optional[str] = None
    onboarded: bool = False
    inventory_onboarded: bool = False


class UserPrefs(BaseModel):
    allergies: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    cuisine_likes: List[str] = Field(default_factory=list)
    servings: int
    meals_per_day: int
    plan_days: int = 0
    cook_time_weekday_mins: Optional[int] = Field(default=None, description="Preferred max cook time on weekdays (minutes)")
    cook_time_weekend_mins: Optional[int] = Field(default=None, description="Preferred max cook time on weekends (minutes)")
    diet_goals: List[str] = Field(default_factory=list, description="Dietary goals e.g. high protein, low sugar")
    equipment: List[str] = Field(default_factory=list, description="Available kitchen equipment e.g. air fryer, slow cooker, instant pot")
    notes: str = ""


class UserPrefsUpsertRequest(BaseModel):
    prefs: UserPrefs


class ProposedUpsertPrefsAction(BaseModel):
    action_type: Literal["upsert_prefs"] = "upsert_prefs"
    prefs: UserPrefs


Unit = Literal[
    "g", "ml", "count",
    "tin", "bag", "box", "jar", "bottle", "pack",
    "loaf", "slice", "piece", "can", "carton", "tub", "pot",
    "bunch", "bulb", "head",
]
Location = Literal["pantry", "fridge", "freezer"]
InventoryEventType = Literal[
    "add",
    "consume_cooked",
    "consume_used_separately",
    "consume_thrown_away",
    "adjust",
]


class InventoryEventCreateRequest(BaseModel):
    occurred_at: Optional[str] = None
    event_type: InventoryEventType
    item_name: str
    quantity: Optional[float] = None
    unit: Optional[Unit] = None
    location: Location = "pantry"
    note: Optional[str] = ""
    source: Optional[str] = "ui"


class InventoryEvent(BaseModel):
    event_id: str
    occurred_at: str
    event_type: InventoryEventType
    item_name: str
    quantity: Optional[float] = None
    unit: Optional[Unit] = None
    location: Location = "pantry"
    note: Optional[str] = None
    source: Optional[str] = None


class InventoryEventListResponse(BaseModel):
    events: List[InventoryEvent]


class InventorySummaryItem(BaseModel):
    item_name: str
    quantity: float
    unit: Unit
    location: Location = "pantry"
    approx: bool = False


class InventorySummaryResponse(BaseModel):
    items: List[InventorySummaryItem]
    generated_at: str


class LowStockItem(BaseModel):
    item_name: str
    quantity: float
    unit: Unit
    threshold: float
    reason: str = ""
    is_staple: bool = False


class LowStockResponse(BaseModel):
    items: List[LowStockItem]
    generated_at: str


class StapleItem(BaseModel):
    item_name: str
    unit: Unit = "count"


class StapleToggleRequest(BaseModel):
    item_name: str = Field(..., min_length=1)
    unit: Unit = "count"


class StapleToggleResponse(BaseModel):
    item_name: str
    unit: Unit
    is_staple: bool


class StaplesListResponse(BaseModel):
    staples: List[StapleItem]


class ProposedInventoryEventAction(BaseModel):
    action_type: Literal["create_inventory_event"] = "create_inventory_event"
    event: InventoryEventCreateRequest


class ProposedGenerateMealPlanAction(BaseModel):
    action_type: Literal["generate_mealplan"] = "generate_mealplan"
    mealplan: MealPlanResponse


MealSlot = Literal["breakfast", "lunch", "dinner", "supper", "snack"]


class IngredientLine(BaseModel):
    item_name: str
    quantity: float
    unit: Unit
    optional: bool = False


class RecipeBookStatus(str, Enum):
    uploading = "uploading"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class RecipeBook(BaseModel):
    book_id: str
    title: str = ""
    filename: str
    content_type: str
    status: RecipeBookStatus
    error_message: Optional[str] = None
    created_at: str
    text_content: Optional[str] = None
    pack_id: Optional[str] = None


class RecipeBookListResponse(BaseModel):
    books: List[RecipeBook]


class RecipePasteRequest(BaseModel):
    title: str = Field("", description="Optional title for the pasted recipe")
    text_content: str = Field(..., min_length=1, description="Recipe text (markdown or plain text)")


class RecipePhotoResponse(BaseModel):
    book_id: str
    status: RecipeBookStatus
    message: str


class BuiltInPack(BaseModel):
    pack_id: str
    label: str
    description: str
    recipe_count: int


class BuiltInPackListResponse(BaseModel):
    packs: List[BuiltInPack]
    installed_pack_ids: List[str] = Field(default_factory=list)


class PackPreviewRecipe(BaseModel):
    title: str
    has_content: bool
    snippet: Optional[str] = None


class PackPreviewResponse(BaseModel):
    pack_id: str
    label: str
    recipes: List[PackPreviewRecipe]
    total_available: int


class InstallPackRequest(BaseModel):
    pack_id: str
    max_recipes: int = Field(default=500, ge=1, le=500)
    selected_titles: Optional[List[str]] = None


class InstallPackResponse(BaseModel):
    installed: int
    books: List[RecipeBook]


class UninstallPackRequest(BaseModel):
    pack_id: str
    selected_titles: Optional[List[str]] = None


class UninstallPackResponse(BaseModel):
    removed: int


class RecipeSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    max_results: int = Field(default=5, ge=1, le=10)


class RecipeSourceType(str, Enum):
    built_in = "built_in"
    user_library = "user_library"


class RecipeSearchResult(BaseModel):
    title: str
    source_type: RecipeSourceType
    built_in_recipe_id: Optional[str] = None
    file_id: Optional[str] = None
    book_id: Optional[str] = None
    excerpt: Optional[str] = None


class RecipeSearchResponse(BaseModel):
    results: List[RecipeSearchResult]


class RecipeSource(BaseModel):
    source_type: RecipeSourceType
    built_in_recipe_id: Optional[str] = None
    file_id: Optional[str] = None
    book_id: Optional[str] = None
    excerpt: Optional[str] = None


class PlannedMeal(BaseModel):
    name: str
    slot: MealSlot
    ingredients: List[IngredientLine]
    instructions: List[str] = Field(default_factory=list)
    source: RecipeSource
    citations: conlist(RecipeSource, min_length=1)


class MealPlanDay(BaseModel):
    day_index: int = Field(..., ge=1)
    meals: List[PlannedMeal]


class MealPlanResponse(BaseModel):
    plan_id: str
    created_at: str
    days: List[MealPlanDay]
    notes: str = ""


class MealPlanGenerateRequest(BaseModel):
    days: int = Field(..., ge=1, le=31)
    meals_per_day: Optional[int] = Field(default=None, ge=1, le=6)
    include_user_library: bool = True
    notes: str = ""


class ShoppingListItem(BaseModel):
    item_name: str
    quantity: float
    unit: Unit
    reason: str = Field(default="needed for plan", min_length=1)
    citations: conlist(RecipeSource, min_length=1)


class ShoppingDiffRequest(BaseModel):
    plan: MealPlanResponse


class ShoppingDiffResponse(BaseModel):
    missing_items: List[ShoppingListItem]
    staple_items: List[ShoppingListItem] = Field(default_factory=list)


class ChatRequest(BaseModel):
    mode: Literal["ask", "fill"]
    message: str = Field(..., min_length=1)
    include_user_library: bool = True
    location: Optional[Literal["pantry", "fridge", "freezer"]] = None
    thread_id: Optional[str] = None
    voice_input: bool = Field(default=False, description="True when message originated from speech-to-text dictation")


class ChatResponse(BaseModel):
    reply_text: str
    confirmation_required: bool
    proposal_id: Optional[str] = None
    proposed_actions: List[Union[ProposedUpsertPrefsAction, ProposedInventoryEventAction, ProposedGenerateMealPlanAction]] = Field(default_factory=list)
    suggested_next_questions: List[str] = Field(default_factory=list)
    mode: Literal["ask", "fill"] = "ask"
    voice_hint: Optional[str] = Field(default=None, description="Short TTS-friendly summary when voice_input was True")


class ConfirmProposalRequest(BaseModel):
    proposal_id: str
    confirm: bool
    thread_id: Optional[str] = None


class ConfirmProposalResponse(BaseModel):
    applied: bool
    applied_event_ids: List[str] = Field(default_factory=list)
    reason: Optional[str] = Field(
        default=None,
        description="Optional machine-readable reason code when `applied` is false.",
    )
