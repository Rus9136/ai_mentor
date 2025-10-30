"""
Pydantic schemas package.
"""

from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    TokenPayload,
)
from app.schemas.textbook import (
    TextbookCreate,
    TextbookUpdate,
    TextbookResponse,
    TextbookListResponse,
)
from app.schemas.chapter import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    ChapterListResponse,
)
from app.schemas.paragraph import (
    ParagraphCreate,
    ParagraphUpdate,
    ParagraphResponse,
    ParagraphListResponse,
)
from app.schemas.test import (
    TestCreate,
    TestUpdate,
    TestResponse,
    TestListResponse,
)
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
    QuestionOptionCreate,
    QuestionOptionUpdate,
    QuestionOptionResponse,
)
from app.schemas.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    SchoolListResponse,
)

__all__ = [
    # Auth
    "LoginRequest",
    "RefreshTokenRequest",
    "TokenResponse",
    "UserResponse",
    "TokenPayload",
    # Textbook
    "TextbookCreate",
    "TextbookUpdate",
    "TextbookResponse",
    "TextbookListResponse",
    # Chapter
    "ChapterCreate",
    "ChapterUpdate",
    "ChapterResponse",
    "ChapterListResponse",
    # Paragraph
    "ParagraphCreate",
    "ParagraphUpdate",
    "ParagraphResponse",
    "ParagraphListResponse",
    # Test
    "TestCreate",
    "TestUpdate",
    "TestResponse",
    "TestListResponse",
    # Question
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    "QuestionListResponse",
    "QuestionOptionCreate",
    "QuestionOptionUpdate",
    "QuestionOptionResponse",
    # School
    "SchoolCreate",
    "SchoolUpdate",
    "SchoolResponse",
    "SchoolListResponse",
]
