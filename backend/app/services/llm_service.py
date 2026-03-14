"""
LLM Service for generating text completions.

Supports multiple providers:
- Cerebras (llama-3.3-70b) - fastest inference, direct API
- OpenRouter (Cerebras, Qwen, Llama) - cost-effective multi-model
- OpenAI (GPT-4, GPT-3.5) - higher quality fallback

Streaming support:
- stream_generate() method returns AsyncIterator for SSE streaming
"""
import json
import logging
import time
from typing import Optional, List, Dict, Any, AsyncIterator
from dataclasses import dataclass, field

import httpx
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


# Cerebras API base URL
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"


@dataclass
class LLMResponse:
    """Response from LLM generation."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass
class LLMStreamChunk:
    """A chunk from streaming LLM generation."""
    content: str
    is_final: bool = False
    tokens_used: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    finish_reason: Optional[str] = None


@dataclass
class LLMUsageContext:
    """Context for automatic LLM usage logging."""
    db: AsyncSession
    feature: str  # LLMFeature value: chat, rag, lesson_plan, etc.
    user_id: Optional[int] = None
    school_id: Optional[int] = None
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None


class LLMServiceError(Exception):
    """Exception for LLM service errors."""
    pass


class OpenRouterClient:
    """
    Client for OpenRouter API.

    OpenRouter provides access to various LLM models including:
    - Cerebras: cerebras/llama-3.3-70b (~$0.50/1M tokens)
    - Qwen: qwen/qwen3-32b
    - Meta: meta-llama/llama-3.3-70b-instruct

    API is compatible with OpenAI's chat completion format.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = base_url or settings.OPENROUTER_BASE_URL
        self.model = model or settings.OPENROUTER_MODEL

        if not self.api_key:
            raise LLMServiceError("OPENROUTER_API_KEY is not configured")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ai-mentor.kz",
                "X-Title": "AI Mentor"
            },
            timeout=60.0
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate text completion using OpenRouter.

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Override default model

        Returns:
            LLMResponse with generated content

        Raises:
            LLMServiceError: If API call fails
        """
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model or self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )

            if response.status_code != 200:
                error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LLMServiceError(error_msg)

            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens")
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            finish_reason = data["choices"][0].get("finish_reason")

            return LLMResponse(
                content=content,
                model=model or self.model,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason
            )

        except httpx.HTTPError as e:
            error_msg = f"OpenRouter request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Stream text completion using OpenRouter.

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Override default model

        Yields:
            LLMStreamChunk with partial content

        Raises:
            LLMServiceError: If API call fails
        """
        try:
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": model or self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                }
            ) as response:
                if response.status_code != 200:
                    content = await response.aread()
                    error_msg = f"OpenRouter API error: {response.status_code} - {content.decode()}"
                    logger.error(error_msg)
                    raise LLMServiceError(error_msg)

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[6:]  # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices") or []
                        if not choices:
                            continue
                        choice = choices[0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        finish_reason = choice.get("finish_reason")

                        if content or finish_reason:
                            yield LLMStreamChunk(
                                content=content,
                                is_final=finish_reason is not None,
                                finish_reason=finish_reason
                            )
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue

        except httpx.HTTPError as e:
            error_msg = f"OpenRouter stream request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class DashScopeClient:
    """
    Client for DashScope API (Alibaba Cloud / Qwen).

    OpenAI-compatible API for direct access to Qwen models.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.base_url = base_url or settings.DASHSCOPE_BASE_URL
        self.model = model or settings.DASHSCOPE_MODEL

        if not self.api_key:
            raise LLMServiceError("DASHSCOPE_API_KEY is not configured")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> LLMResponse:
        try:
            payload = {
                "model": model or self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "enable_thinking": False
            }
            response = await self.client.post(
                "/chat/completions",
                json=payload
            )

            if response.status_code != 200:
                error_msg = f"DashScope API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LLMServiceError(error_msg)

            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens")
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            finish_reason = data["choices"][0].get("finish_reason")

            return LLMResponse(
                content=content,
                model=model or self.model,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason
            )

        except httpx.HTTPError as e:
            error_msg = f"DashScope request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> AsyncIterator[LLMStreamChunk]:
        try:
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json={
                    "model": model or self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                    "stream_options": {"include_usage": True},
                    "enable_thinking": False
                }
            ) as response:
                if response.status_code != 200:
                    content = await response.aread()
                    error_msg = f"DashScope API error: {response.status_code} - {content.decode()}"
                    logger.error(error_msg)
                    raise LLMServiceError(error_msg)

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices") or []
                        if not choices:
                            continue
                        choice = choices[0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        finish_reason = choice.get("finish_reason")

                        if content or finish_reason:
                            usage = data.get("usage")
                            yield LLMStreamChunk(
                                content=content,
                                is_final=finish_reason is not None,
                                tokens_used=usage.get("total_tokens") if usage else None,
                                prompt_tokens=usage.get("prompt_tokens") if usage else None,
                                completion_tokens=usage.get("completion_tokens") if usage else None,
                                finish_reason=finish_reason
                            )
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue

        except httpx.HTTPError as e:
            error_msg = f"DashScope stream request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)

    async def close(self):
        await self.client.aclose()


class CerebrasClient:
    """
    Client for Cerebras API (direct access).

    Cerebras provides extremely fast inference with llama-3.3-70b.
    API is OpenAI-compatible.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.CEREBRAS_API_KEY
        self.model = model or settings.CEREBRAS_MODEL

        if not self.api_key:
            raise LLMServiceError("CEREBRAS_API_KEY is not configured")

        self.client = httpx.AsyncClient(
            base_url=CEREBRAS_BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate text completion using Cerebras.

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Override default model

        Returns:
            LLMResponse with generated content

        Raises:
            LLMServiceError: If API call fails
        """
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model or self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )

            if response.status_code != 200:
                error_msg = f"Cerebras API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise LLMServiceError(error_msg)

            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens")
            prompt_tokens = usage.get("prompt_tokens")
            completion_tokens = usage.get("completion_tokens")
            finish_reason = data["choices"][0].get("finish_reason")

            return LLMResponse(
                content=content,
                model=model or self.model,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason
            )

        except httpx.HTTPError as e:
            error_msg = f"Cerebras request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class OpenAIClient:
    """
    Client for OpenAI API.

    Used as fallback when other providers are unavailable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.LLM_MODEL

        if not self.api_key:
            raise LLMServiceError("OPENAI_API_KEY is not configured")

        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate text completion using OpenAI.

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Override default model

        Returns:
            LLMResponse with generated content

        Raises:
            LLMServiceError: If API call fails
        """
        try:
            response = await self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            prompt_tokens = response.usage.prompt_tokens if response.usage else None
            completion_tokens = response.usage.completion_tokens if response.usage else None
            finish_reason = response.choices[0].finish_reason

            return LLMResponse(
                content=content,
                model=model or self.model,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=finish_reason
            )

        except Exception as e:
            error_msg = f"OpenAI request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)


class LLMService:
    """
    Unified LLM Service with provider switching and fallback.

    Usage:
        llm = LLMService()
        response = await llm.generate(messages=[
            {"role": "system", "content": "You are a helpful tutor."},
            {"role": "user", "content": "Explain photosynthesis."}
        ])
        print(response.content)
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM service.

        Args:
            provider: LLM provider to use ('dashscope', 'cerebras', 'openrouter', or 'openai')
                     Defaults to settings.LLM_PROVIDER
        """
        self.provider = provider or settings.LLM_PROVIDER
        self._dashscope_client: Optional[DashScopeClient] = None
        self._cerebras_client: Optional[CerebrasClient] = None
        self._openrouter_client: Optional[OpenRouterClient] = None
        self._openai_client: Optional[OpenAIClient] = None
        self._openrouter_fallback: Optional[OpenRouterClient] = None

    def _get_client(self):
        """Get or create the appropriate LLM client."""
        if self.provider == "dashscope":
            if self._dashscope_client is None:
                self._dashscope_client = DashScopeClient()
            return self._dashscope_client
        elif self.provider == "cerebras":
            if self._cerebras_client is None:
                self._cerebras_client = CerebrasClient()
            return self._cerebras_client
        elif self.provider == "openrouter":
            if self._openrouter_client is None:
                self._openrouter_client = OpenRouterClient()
            return self._openrouter_client
        else:
            if self._openai_client is None:
                self._openai_client = OpenAIClient()
            return self._openai_client

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None,
        fallback_on_error: bool = True,
        usage_context: Optional[LLMUsageContext] = None,
    ) -> LLMResponse:
        """
        Generate text completion.

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Override default model
            fallback_on_error: If True, try fallback provider on error
            usage_context: If provided, auto-log usage to llm_usage_logs

        Returns:
            LLMResponse with generated content

        Raises:
            LLMServiceError: If all providers fail
        """
        start = time.monotonic()
        try:
            client = self._get_client()
            response = await client.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            if usage_context:
                await self._log_usage(usage_context, response, latency_ms)
            return response
        except LLMServiceError as e:
            if not (fallback_on_error and self.provider in ("dashscope", "cerebras")):
                latency_ms = int((time.monotonic() - start) * 1000)
                if usage_context:
                    await self._log_usage_error(usage_context, model or self.provider, latency_ms, str(e))
                raise

            # Fallback 1 (cerebras only): Try Cerebras with gpt-oss-120b
            if self.provider == "cerebras":
                cerebras_fallback_model = "gpt-oss-120b"
                used_model = model or self._get_client().model
                if used_model != cerebras_fallback_model:
                    logger.warning(f"Cerebras {used_model} failed, trying Cerebras {cerebras_fallback_model}: {str(e)}")
                    try:
                        client = self._get_client()
                        response = await client.generate(
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            model=cerebras_fallback_model
                        )
                        latency_ms = int((time.monotonic() - start) * 1000)
                        if usage_context:
                            await self._log_usage(usage_context, response, latency_ms)
                        return response
                    except LLMServiceError as e2:
                        logger.warning(f"Cerebras {cerebras_fallback_model} also failed: {str(e2)}")

            # Fallback 2: Try OpenRouter
            logger.warning(f"{self.provider} unavailable, trying OpenRouter fallback")
            try:
                if self._openrouter_fallback is None:
                    self._openrouter_fallback = OpenRouterClient()
                response = await self._openrouter_fallback.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                latency_ms = int((time.monotonic() - start) * 1000)
                if usage_context:
                    await self._log_usage(usage_context, response, latency_ms)
                return response
            except LLMServiceError:
                pass  # Re-raise original error

            latency_ms = int((time.monotonic() - start) * 1000)
            if usage_context:
                await self._log_usage_error(usage_context, model or self.provider, latency_ms, str(e))
            raise

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Stream text completion.

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Override default model

        Yields:
            LLMStreamChunk with partial content

        Raises:
            LLMServiceError: If provider fails or doesn't support streaming
        """
        # DashScope and OpenRouter support streaming
        if self.provider in ("openrouter", "dashscope"):
            client = self._get_client()
            yielded_any = False
            try:
                async for chunk in client.stream_generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model
                ):
                    yielded_any = True
                    yield chunk
            except (LLMServiceError, Exception) as e:
                if yielded_any or self.provider == "openrouter":
                    raise  # Can't fallback mid-stream or for openrouter
                # Fallback to OpenRouter streaming
                logger.warning(f"{self.provider} stream failed, trying OpenRouter fallback: {e}")
                try:
                    if self._openrouter_fallback is None:
                        self._openrouter_fallback = OpenRouterClient()
                    async for chunk in self._openrouter_fallback.stream_generate(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    ):
                        yield chunk
                except LLMServiceError:
                    raise  # Both providers failed
        else:
            # Fallback: generate full response and yield as single chunk
            response = await self.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
                fallback_on_error=True
            )
            yield LLMStreamChunk(
                content=response.content,
                is_final=True,
                tokens_used=response.tokens_used,
                finish_reason=response.finish_reason
            )

    async def _log_usage(
        self,
        ctx: LLMUsageContext,
        response: LLMResponse,
        latency_ms: int,
    ) -> None:
        """Log successful LLM usage to database."""
        try:
            from app.models.llm_usage_log import LLMUsageLog
            from sqlalchemy import text as sa_text
            async with ctx.db.begin_nested():
                if ctx.school_id:
                    await ctx.db.execute(sa_text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": str(ctx.school_id)})
                log = LLMUsageLog(
                    user_id=ctx.user_id,
                    school_id=ctx.school_id,
                    student_id=ctx.student_id,
                    teacher_id=ctx.teacher_id,
                    feature=ctx.feature,
                    provider=self.provider,
                    model=response.model,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    total_tokens=response.tokens_used,
                    latency_ms=latency_ms,
                    success=True,
                )
                ctx.db.add(log)
                await ctx.db.flush()
                # Increment daily usage counter
                if ctx.user_id:
                    from app.repositories.usage_repo import UsageRepository
                    usage_repo = UsageRepository(ctx.db)
                    await usage_repo.increment_counter(
                        user_id=ctx.user_id,
                        school_id=ctx.school_id,
                        feature=ctx.feature,
                        tokens=response.tokens_used or 0,
                    )
        except Exception as e:
            logger.warning(f"Failed to log LLM usage: {e}")

    async def _log_usage_error(
        self,
        ctx: LLMUsageContext,
        model: str,
        latency_ms: int,
        error_message: str,
    ) -> None:
        """Log failed LLM usage to database."""
        try:
            from app.models.llm_usage_log import LLMUsageLog
            from sqlalchemy import text as sa_text
            async with ctx.db.begin_nested():
                if ctx.school_id:
                    await ctx.db.execute(sa_text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": str(ctx.school_id)})
                log = LLMUsageLog(
                    user_id=ctx.user_id,
                    school_id=ctx.school_id,
                    student_id=ctx.student_id,
                    teacher_id=ctx.teacher_id,
                    feature=ctx.feature,
                    provider=self.provider,
                    model=model,
                    latency_ms=latency_ms,
                    success=False,
                    error_message=error_message[:500],
                )
                ctx.db.add(log)
                await ctx.db.flush()
        except Exception as e:
            logger.warning(f"Failed to log LLM usage error: {e}")

    async def close(self):
        """Close all clients."""
        if self._dashscope_client:
            await self._dashscope_client.close()
        if self._cerebras_client:
            await self._cerebras_client.close()
        if self._openrouter_client:
            await self._openrouter_client.close()
