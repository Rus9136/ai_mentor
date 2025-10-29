"""
Offline sync models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import BaseModel


class SyncStatus(str, enum.Enum):
    """Sync status enumeration."""

    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncQueue(BaseModel):
    """Sync queue model for offline data synchronization."""

    __tablename__ = "sync_queue"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sync info
    entity_type = Column(String(100), nullable=False, index=True)  # e.g., "test_attempt", "learning_activity"
    entity_id = Column(Integer, nullable=True)  # ID of the entity to sync
    operation = Column(String(20), nullable=False)  # create, update, delete
    data = Column(Text, nullable=False)  # JSON data to sync

    # Status
    status = Column(SQLEnum(SyncStatus), nullable=False, default=SyncStatus.PENDING, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    # Device info
    device_id = Column(String(255), nullable=True)
    created_at_device = Column(DateTime(timezone=True), nullable=False)  # When created on device

    def __repr__(self) -> str:
        return f"<SyncQueue(id={self.id}, type='{self.entity_type}', status='{self.status}')>"
