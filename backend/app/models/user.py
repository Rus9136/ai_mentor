"""
User models.
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import SoftDeleteModel


class UserRole(str, enum.Enum):
    """User role enumeration."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class User(SoftDeleteModel):
    """User model."""

    __tablename__ = "users"

    # School relationship (tenant) - nullable for SUPER_ADMIN
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)

    # Authentication
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)

    # Role
    role = Column(SQLEnum(UserRole), nullable=False, index=True)

    # Relationships
    school = relationship("School", back_populates="users")
    student = relationship("Student", back_populates="user", uselist=False)
    teacher = relationship("Teacher", back_populates="user", uselist=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    @property
    def full_name(self) -> str:
        """Get full name."""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)
