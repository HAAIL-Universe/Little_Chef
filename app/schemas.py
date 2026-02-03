from pydantic import BaseModel, Field
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


class UserPrefs(BaseModel):
    allergies: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    cuisine_likes: List[str] = Field(default_factory=list)
    servings: int
    meals_per_day: int
    notes: str = ""


class UserPrefsUpsertRequest(BaseModel):
    prefs: UserPrefs


class ProposedUpsertPrefsAction(BaseModel):
    action_type: Literal["upsert_prefs"] = "upsert_prefs"
    prefs: UserPrefs


Unit = Literal["g", "ml", "count"]
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
    quantity: float
    unit: Unit
    note: Optional[str] = ""
    source: Optional[str] = "ui"


class InventoryEvent(BaseModel):
    event_id: str
    occurred_at: str
    event_type: InventoryEventType
    item_name: str
    quantity: float
    unit: Unit
    note: Optional[str] = None
    source: Optional[str] = None


class InventoryEventListResponse(BaseModel):
    events: List[InventoryEvent]


class InventorySummaryItem(BaseModel):
    item_name: str
    quantity: float
    unit: Unit
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


class LowStockResponse(BaseModel):
    items: List[LowStockItem]
    generated_at: str


class ProposedInventoryEventAction(BaseModel):
    action_type: Literal["create_inventory_event"] = "create_inventory_event"
    event: InventoryEventCreateRequest


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


class RecipeBookListResponse(BaseModel):
    books: List[RecipeBook]


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
    reason: str = ""


class ShoppingDiffRequest(BaseModel):
    plan: MealPlanResponse


class ShoppingDiffResponse(BaseModel):
    missing_items: List[ShoppingListItem]


class ChatRequest(BaseModel):
    mode: Literal["ask", "fill"]
    message: str = Field(..., min_length=1)
    include_user_library: bool = True


class ChatResponse(BaseModel):
    reply_text: str
    confirmation_required: bool
    proposal_id: Optional[str] = None
    proposed_actions: List[Union[ProposedUpsertPrefsAction, ProposedInventoryEventAction]] = Field(default_factory=list)
    suggested_next_questions: List[str] = Field(default_factory=list)


class ConfirmProposalRequest(BaseModel):
    proposal_id: str
    confirm: bool


class ConfirmProposalResponse(BaseModel):
    applied: bool
    applied_event_ids: List[str] = Field(default_factory=list)
