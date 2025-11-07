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
    QuestionOptionResponseStudent,
    QuestionResponseStudent,
)
from app.schemas.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    SchoolListResponse,
)
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponseSchema,
    UserListResponse,
)
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
)
from app.schemas.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    TeacherListResponse,
)
from app.schemas.parent import (
    ParentCreate,
    ParentUpdate,
    ParentResponse,
    ParentListResponse,
    AddChildrenRequest,
)
from app.schemas.school_class import (
    SchoolClassCreate,
    SchoolClassUpdate,
    SchoolClassResponse,
    SchoolClassListResponse,
    AddStudentsRequest,
    AddTeachersRequest,
)
from app.schemas.upload import (
    ImageUploadResponse,
    PDFUploadResponse,
)
from app.schemas.test_attempt import (
    AnswerSubmit,
    TestAttemptCreate,
    TestAttemptSubmit,
    TestAttemptAnswerResponse,
    TestAttemptResponse,
    TestAttemptDetailResponse,
    StudentProgressResponse,
    AvailableTestResponse,
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
    "QuestionOptionResponseStudent",
    "QuestionResponseStudent",
    # School
    "SchoolCreate",
    "SchoolUpdate",
    "SchoolResponse",
    "SchoolListResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponseSchema",
    "UserListResponse",
    # Student
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "StudentListResponse",
    # Teacher
    "TeacherCreate",
    "TeacherUpdate",
    "TeacherResponse",
    "TeacherListResponse",
    # Parent
    "ParentCreate",
    "ParentUpdate",
    "ParentResponse",
    "ParentListResponse",
    "AddChildrenRequest",
    # SchoolClass
    "SchoolClassCreate",
    "SchoolClassUpdate",
    "SchoolClassResponse",
    "SchoolClassListResponse",
    "AddStudentsRequest",
    "AddTeachersRequest",
    # Upload
    "ImageUploadResponse",
    "PDFUploadResponse",
    # TestAttempt
    "AnswerSubmit",
    "TestAttemptCreate",
    "TestAttemptSubmit",
    "TestAttemptAnswerResponse",
    "TestAttemptResponse",
    "TestAttemptDetailResponse",
    "StudentProgressResponse",
    "AvailableTestResponse",
]
