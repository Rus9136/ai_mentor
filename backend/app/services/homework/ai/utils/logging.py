"""
AI operation logging utilities.
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import AIGenerationLog


async def log_ai_operation(
    db: AsyncSession,
    operation_type: str,
    input_context: Dict[str, Any],
    prompt_used: str,
    parsed_output: Dict[str, Any],
    model_used: str,
    tokens_used: int,
    latency_ms: float,
    success: bool = True,
    task_id: Optional[int] = None,
    answer_id: Optional[int] = None
) -> None:
    """
    Log AI operation for analytics.

    Args:
        db: Database session
        operation_type: Type of operation (question_generation, answer_grading)
        input_context: Input parameters dict
        prompt_used: Prompt sent to LLM
        parsed_output: Parsed result dict
        model_used: LLM model identifier
        tokens_used: Total tokens used
        latency_ms: Operation latency in milliseconds
        success: Whether operation succeeded
        task_id: Optional task ID
        answer_id: Optional answer ID
    """
    log = AIGenerationLog(
        operation_type=operation_type,
        input_context=input_context,
        prompt_used=prompt_used[:10000],  # Truncate if too long
        parsed_output=parsed_output,
        model_used=model_used,
        tokens_input=tokens_used // 2,  # Approximate split
        tokens_output=tokens_used // 2,
        latency_ms=int(latency_ms),
        success=success,
        homework_task_id=task_id
    )
    db.add(log)
    await db.flush()
