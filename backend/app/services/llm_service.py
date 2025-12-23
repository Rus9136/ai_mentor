"""
LLM Service for generating text completions.

Supports multiple providers:
- Cerebras (llama-3.3-70b) - fastest inference, direct API
- OpenRouter (Cerebras, Qwen, Llama) - cost-effective multi-model
- OpenAI (GPT-4, GPT-3.5) - higher quality fallback
"""
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI

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
    finish_reason: Optional[str] = None


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
        self.model = model or settings.CEREBRAS_MODEL

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
            tokens_used = data.get("usage", {}).get("total_tokens")
            finish_reason = data["choices"][0].get("finish_reason")

            return LLMResponse(
                content=content,
                model=model or self.model,
                tokens_used=tokens_used,
                finish_reason=finish_reason
            )

        except httpx.HTTPError as e:
            error_msg = f"OpenRouter request failed: {str(e)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)

    async def close(self):
        """Close the HTTP client."""
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
        self.api_key = api_key or settings.OPENROUTER_API_KEY  # Uses same key field
        self.model = model or "llama-3.3-70b"  # Cerebras model name (without provider prefix)

        if not self.api_key:
            raise LLMServiceError("CEREBRAS/OPENROUTER_API_KEY is not configured")

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
            tokens_used = data.get("usage", {}).get("total_tokens")
            finish_reason = data["choices"][0].get("finish_reason")

            return LLMResponse(
                content=content,
                model=model or self.model,
                tokens_used=tokens_used,
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
            finish_reason = response.choices[0].finish_reason

            return LLMResponse(
                content=content,
                model=model or self.model,
                tokens_used=tokens_used,
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
            provider: LLM provider to use ('cerebras', 'openrouter', or 'openai')
                     Defaults to settings.LLM_PROVIDER
        """
        self.provider = provider or settings.LLM_PROVIDER
        self._cerebras_client: Optional[CerebrasClient] = None
        self._openrouter_client: Optional[OpenRouterClient] = None
        self._openai_client: Optional[OpenAIClient] = None

    def _get_client(self):
        """Get or create the appropriate LLM client."""
        if self.provider == "cerebras":
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
        fallback_on_error: bool = True
    ) -> LLMResponse:
        """
        Generate text completion.

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            model: Override default model
            fallback_on_error: If True, try fallback provider on error

        Returns:
            LLMResponse with generated content

        Raises:
            LLMServiceError: If all providers fail
        """
        try:
            client = self._get_client()
            return await client.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model
            )
        except LLMServiceError as e:
            if fallback_on_error and self.provider in ("cerebras", "openrouter"):
                # Try OpenAI as fallback
                logger.warning(f"{self.provider} failed, trying OpenAI fallback: {str(e)}")
                try:
                    if self._openai_client is None:
                        self._openai_client = OpenAIClient()
                    return await self._openai_client.generate(
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                except LLMServiceError:
                    pass  # Re-raise original error

            raise

    async def close(self):
        """Close all clients."""
        if self._cerebras_client:
            await self._cerebras_client.close()
        if self._openrouter_client:
            await self._openrouter_client.close()
