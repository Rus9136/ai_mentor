"""
System prompt templates for AI chat personalization.

Allows admins to edit prompts without code deployment.
"""
from sqlalchemy import Column, String, Text, Boolean, Integer

from app.models.base import BaseModel


class SystemPromptTemplate(BaseModel):
    """
    System prompt template model.

    Stores customizable system prompts for different:
    - Session types (reading_help, post_paragraph, test_help, general_tutor)
    - Mastery levels (A, B, C)
    - Languages (ru, kk)

    Only one active prompt per (type, level, language) combination.
    """

    __tablename__ = "system_prompt_templates"

    # Prompt identification
    prompt_type = Column(
        String(50),
        nullable=False,
        index=True
    )  # reading_help, post_paragraph, test_help, general_tutor

    mastery_level = Column(
        String(1),
        nullable=False,
        index=True
    )  # A, B, C

    language = Column(
        String(5),
        nullable=False,
        default="ru"
    )  # ru, kk

    # Prompt content
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    prompt_text = Column(Text, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)

    def __repr__(self) -> str:
        return f"<SystemPromptTemplate(type='{self.prompt_type}', level='{self.mastery_level}', lang='{self.language}')>"
