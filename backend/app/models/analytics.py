"""
Analytics models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class AnalyticsEvent(BaseModel):
    """Analytics event model."""

    __tablename__ = "analytics_events"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)

    # Event info
    event_type = Column(String(100), nullable=False, index=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    event_data = Column(JSON, nullable=True)  # Event-specific data

    # User context
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    device_type = Column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, type='{self.event_type}', timestamp={self.event_timestamp})>"
