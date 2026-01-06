"""
AI utilities package.
"""

from app.services.homework.ai.utils.json_parser import (
    parse_json_array,
    parse_json_object,
    strip_markdown_code_blocks,
)
from app.services.homework.ai.utils.logging import log_ai_operation
from app.services.homework.ai.utils.prompt_builder import (
    build_generation_prompt,
    build_grading_prompt,
    get_generation_system_prompt,
    get_grading_system_prompt,
)

__all__ = [
    "strip_markdown_code_blocks",
    "parse_json_array",
    "parse_json_object",
    "get_generation_system_prompt",
    "build_generation_prompt",
    "get_grading_system_prompt",
    "build_grading_prompt",
    "log_ai_operation",
]
