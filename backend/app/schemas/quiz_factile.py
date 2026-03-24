"""
Schemas for Factile (Jeopardy-style) quiz mode.

Board structure:
- Up to 6 categories (columns)
- Up to 5 questions per category (rows) with increasing point values
- Two teams take turns selecting cells
- Teacher judges answers manually
"""
from typing import Optional
from pydantic import BaseModel, Field


# ── Board definition (used at creation time) ──

class FactileCategoryInput(BaseModel):
    """A category column for the Factile board."""
    name: str = Field(min_length=1, max_length=100, description="Category display name")
    question_ids: list[int] = Field(
        min_length=1, max_length=5,
        description="Question IDs for this category, ordered by difficulty (easy→hard)",
    )


class FactileCreateRequest(BaseModel):
    """Request to create a Factile quiz session."""
    class_id: Optional[int] = None
    categories: list[FactileCategoryInput] = Field(
        min_length=2, max_length=6,
        description="2-6 categories for the board",
    )
    point_values: list[int] = Field(
        default=[100, 200, 300, 400, 500],
        min_length=1, max_length=5,
        description="Point values per row (applied to all categories)",
    )
    team_names: Optional[list[str]] = Field(
        default=None,
        description="Custom team names (exactly 2). Defaults to predefined names.",
    )


# ── Board state (runtime, stored in quiz_sessions.board_state) ──

class FactileCellState(BaseModel):
    """State of a single cell on the board."""
    question_id: int
    points: int
    status: str = "available"  # available | active | answered | skipped
    answered_by_team_id: Optional[int] = None
    is_correct: Optional[bool] = None


class FactileCategoryState(BaseModel):
    """State of a category column."""
    name: str
    cells: list[FactileCellState]


class FactileBoardState(BaseModel):
    """Full board state for a Factile session."""
    categories: list[FactileCategoryState]
    team_ids: list[int]  # [team_0_id, team_1_id]
    current_team_index: int = 0  # 0 or 1
    active_cell: Optional[dict] = None  # {"category": int, "row": int}
    cells_remaining: int = 0
    pass_to_other: bool = False  # True when wrong answer, other team can try


# ── WS message payloads ──

class FactileBoardMessage(BaseModel):
    """Board state broadcast to all clients."""
    categories: list[dict]  # simplified for WS
    team_scores: list[dict]  # [{id, name, color, score}]
    current_team_index: int
    current_team_name: str
    cells_remaining: int


class FactileCellSelectedMessage(BaseModel):
    """Broadcast when a cell is opened."""
    category_index: int
    category_name: str
    row_index: int
    points: int
    question: dict  # {text, options, question_type, image_url}
    team_name: str  # team that selected this cell


class FactileJudgeResultMessage(BaseModel):
    """Broadcast after teacher judges an answer."""
    is_correct: bool
    points: int
    team_name: str
    team_scores: list[dict]
    next_team_name: str
    pass_to_other: bool  # if wrong, other team can try
    cells_remaining: int


class FactileAnswerRevealedMessage(BaseModel):
    """Broadcast when teacher reveals the correct answer."""
    correct_option: int
    correct_text: str


class FactileFinishedMessage(BaseModel):
    """Broadcast when all cells are played."""
    team_scores: list[dict]
    winner_team_name: str
    winner_team_id: int
