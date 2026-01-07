"""
Tests for LLM Service.

Tests cover:
- OpenRouterClient
- CerebrasClient
- OpenAIClient
- LLMService (unified service with fallback)
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from dataclasses import dataclass

from app.services.llm_service import (
    LLMService,
    LLMResponse,
    LLMServiceError,
    OpenRouterClient,
    CerebrasClient,
    OpenAIClient,
)


# ========== Mock Response Helpers ==========

def create_mock_httpx_response(status_code: int, json_data: dict = None, text: str = ""):
    """Create a mock httpx response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = text
    if json_data:
        mock_response.json.return_value = json_data
    return mock_response


def create_success_response(content: str = "Generated text", model: str = "test-model"):
    """Create a successful LLM response dict."""
    return {
        "choices": [
            {
                "message": {"content": content},
                "finish_reason": "stop"
            }
        ],
        "usage": {"total_tokens": 150}
    }


# ========== OpenRouterClient Tests ==========

class TestOpenRouterClient:
    """Tests for OpenRouterClient."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation via OpenRouter."""
        mock_response = create_mock_httpx_response(
            200,
            create_success_response("Hello from OpenRouter!")
        )

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")
                response = await client.generate(
                    messages=[{"role": "user", "content": "Hello"}]
                )

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from OpenRouter!"
        assert response.tokens_used == 150
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_custom_temperature(self):
        """Test generation with custom temperature."""
        mock_response = create_mock_httpx_response(200, create_success_response())

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")
                await client.generate(
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=0.3
                )

        # Verify temperature was passed
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_generate_custom_max_tokens(self):
        """Test generation with custom max_tokens."""
        mock_response = create_mock_httpx_response(200, create_success_response())

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")
                await client.generate(
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=2000
                )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["max_tokens"] == 2000

    @pytest.mark.asyncio
    async def test_generate_custom_model(self):
        """Test generation with custom model override."""
        mock_response = create_mock_httpx_response(200, create_success_response())

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "default-model"

                client = OpenRouterClient(api_key="test-api-key")
                response = await client.generate(
                    messages=[{"role": "user", "content": "Hello"}],
                    model="custom-model"
                )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["model"] == "custom-model"
        assert response.model == "custom-model"

    @pytest.mark.asyncio
    async def test_generate_api_error_400(self):
        """Test handling of 400 Bad Request."""
        mock_response = create_mock_httpx_response(400, text="Bad Request")

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")

                with pytest.raises(LLMServiceError) as exc_info:
                    await client.generate(
                        messages=[{"role": "user", "content": "Hello"}]
                    )

        assert "400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_api_error_500(self):
        """Test handling of 500 Internal Server Error."""
        mock_response = create_mock_httpx_response(500, text="Internal Server Error")

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")

                with pytest.raises(LLMServiceError) as exc_info:
                    await client.generate(
                        messages=[{"role": "user", "content": "Hello"}]
                    )

        assert "500" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_timeout(self):
        """Test handling of request timeout."""
        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Connection timed out"))
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")

                with pytest.raises(LLMServiceError) as exc_info:
                    await client.generate(
                        messages=[{"role": "user", "content": "Hello"}]
                    )

        assert "failed" in str(exc_info.value).lower()

    def test_no_api_key_raises_error(self):
        """Test that missing API key raises error."""
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = None
            mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
            mock_settings.CEREBRAS_MODEL = "test-model"

            with pytest.raises(LLMServiceError) as exc_info:
                OpenRouterClient()

        assert "not configured" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        """Test that close() closes the HTTP client."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.aclose = AsyncMock()
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")
                await client.close()

        mock_client.aclose.assert_called_once()


# ========== CerebrasClient Tests ==========

class TestCerebrasClient:
    """Tests for CerebrasClient."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation via Cerebras."""
        mock_response = create_mock_httpx_response(
            200,
            create_success_response("Hello from Cerebras!")
        )

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"

                client = CerebrasClient(api_key="test-api-key")
                response = await client.generate(
                    messages=[{"role": "user", "content": "Hello"}]
                )

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from Cerebras!"

    @pytest.mark.asyncio
    async def test_generate_uses_cerebras_base_url(self):
        """Test that Cerebras client uses correct base URL."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"

                CerebrasClient(api_key="test-api-key")

        # Check that CEREBRAS_BASE_URL was used
        call_kwargs = MockClient.call_args[1]
        assert "cerebras.ai" in call_kwargs["base_url"]

    @pytest.mark.asyncio
    async def test_generate_api_error(self):
        """Test handling of API error."""
        mock_response = create_mock_httpx_response(429, text="Rate limited")

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"

                client = CerebrasClient(api_key="test-api-key")

                with pytest.raises(LLMServiceError):
                    await client.generate(
                        messages=[{"role": "user", "content": "Hello"}]
                    )

    def test_no_api_key_raises_error(self):
        """Test that missing API key raises error."""
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.OPENROUTER_API_KEY = None

            with pytest.raises(LLMServiceError):
                CerebrasClient()


# ========== OpenAIClient Tests ==========

class TestOpenAIClient:
    """Tests for OpenAIClient."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful generation via OpenAI."""
        # Create mock OpenAI response
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from OpenAI!"
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 100

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        with patch("openai.AsyncOpenAI") as MockOpenAI:
            mock_openai = MagicMock()
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
            MockOpenAI.return_value = mock_openai

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.LLM_MODEL = "gpt-4"

                client = OpenAIClient(api_key="test-api-key")
                response = await client.generate(
                    messages=[{"role": "user", "content": "Hello"}]
                )

        assert isinstance(response, LLMResponse)
        assert response.content == "Hello from OpenAI!"
        assert response.tokens_used == 100
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_uses_openai_sdk(self):
        """Test that OpenAI SDK is used correctly."""
        mock_choice = MagicMock()
        mock_choice.message.content = "Test"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None

        with patch("openai.AsyncOpenAI") as MockOpenAI:
            mock_openai = MagicMock()
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
            MockOpenAI.return_value = mock_openai

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.LLM_MODEL = "gpt-4"

                client = OpenAIClient(api_key="test-api-key")
                await client.generate(
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=0.5,
                    max_tokens=1000
                )

        # Verify SDK was called correctly
        mock_openai.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai.chat.completions.create.call_args[1]
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 1000

    @pytest.mark.asyncio
    async def test_generate_error(self):
        """Test handling of OpenAI API error."""
        with patch("openai.AsyncOpenAI") as MockOpenAI:
            mock_openai = MagicMock()
            mock_openai.chat.completions.create = AsyncMock(
                side_effect=Exception("API Error")
            )
            MockOpenAI.return_value = mock_openai

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.LLM_MODEL = "gpt-4"

                client = OpenAIClient(api_key="test-api-key")

                with pytest.raises(LLMServiceError):
                    await client.generate(
                        messages=[{"role": "user", "content": "Hello"}]
                    )

    def test_no_api_key_raises_error(self):
        """Test that missing API key raises error."""
        with patch("app.services.llm_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.LLM_MODEL = "gpt-4"

            with pytest.raises(LLMServiceError):
                OpenAIClient()


# ========== LLMService Tests ==========

class TestLLMService:
    """Tests for unified LLMService."""

    @pytest.mark.asyncio
    async def test_generate_uses_default_provider(self):
        """Test that generate uses default provider from settings."""
        mock_response = create_mock_httpx_response(200, create_success_response())

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.LLM_PROVIDER = "cerebras"
                mock_settings.OPENROUTER_API_KEY = "test-api-key"

                service = LLMService()
                response = await service.generate(
                    messages=[{"role": "user", "content": "Hello"}]
                )

        assert isinstance(response, LLMResponse)

    @pytest.mark.asyncio
    async def test_generate_cerebras_provider(self):
        """Test generation with Cerebras provider."""
        mock_response = create_mock_httpx_response(200, create_success_response("Cerebras response"))

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"

                service = LLMService(provider="cerebras")
                response = await service.generate(
                    messages=[{"role": "user", "content": "Hello"}]
                )

        assert response.content == "Cerebras response"

    @pytest.mark.asyncio
    async def test_generate_openrouter_provider(self):
        """Test generation with OpenRouter provider."""
        mock_response = create_mock_httpx_response(200, create_success_response("OpenRouter response"))

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                service = LLMService(provider="openrouter")
                response = await service.generate(
                    messages=[{"role": "user", "content": "Hello"}]
                )

        assert response.content == "OpenRouter response"

    @pytest.mark.asyncio
    async def test_generate_openai_provider(self):
        """Test generation with OpenAI provider."""
        mock_choice = MagicMock()
        mock_choice.message.content = "OpenAI response"
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None

        with patch("openai.AsyncOpenAI") as MockOpenAI:
            mock_openai = MagicMock()
            mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
            MockOpenAI.return_value = mock_openai

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENAI_API_KEY = "test-api-key"
                mock_settings.LLM_MODEL = "gpt-4"

                service = LLMService(provider="openai")
                response = await service.generate(
                    messages=[{"role": "user", "content": "Hello"}]
                )

        assert response.content == "OpenAI response"

    @pytest.mark.asyncio
    async def test_generate_fallback_on_error(self):
        """Test that fallback to OpenAI works when primary provider fails."""
        # Create mock that fails for Cerebras but succeeds for OpenAI
        mock_httpx_response = create_mock_httpx_response(500, text="Server Error")

        mock_choice = MagicMock()
        mock_choice.message.content = "Fallback response"
        mock_choice.finish_reason = "stop"

        mock_openai_response = MagicMock()
        mock_openai_response.choices = [mock_choice]
        mock_openai_response.usage = None

        with patch("httpx.AsyncClient") as MockHttpxClient:
            mock_httpx = AsyncMock()
            mock_httpx.post = AsyncMock(return_value=mock_httpx_response)
            MockHttpxClient.return_value = mock_httpx

            with patch("openai.AsyncOpenAI") as MockOpenAI:
                mock_openai = MagicMock()
                mock_openai.chat.completions.create = AsyncMock(return_value=mock_openai_response)
                MockOpenAI.return_value = mock_openai

                with patch("app.services.llm_service.settings") as mock_settings:
                    mock_settings.OPENROUTER_API_KEY = "test-api-key"
                    mock_settings.OPENAI_API_KEY = "test-openai-key"
                    mock_settings.LLM_MODEL = "gpt-4"

                    service = LLMService(provider="cerebras")
                    response = await service.generate(
                        messages=[{"role": "user", "content": "Hello"}],
                        fallback_on_error=True
                    )

        assert response.content == "Fallback response"

    @pytest.mark.asyncio
    async def test_generate_no_fallback_when_disabled(self):
        """Test that fallback is not used when disabled."""
        mock_response = create_mock_httpx_response(500, text="Server Error")

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"

                service = LLMService(provider="cerebras")

                with pytest.raises(LLMServiceError):
                    await service.generate(
                        messages=[{"role": "user", "content": "Hello"}],
                        fallback_on_error=False
                    )

    @pytest.mark.asyncio
    async def test_generate_all_providers_fail(self):
        """Test that error is raised when all providers fail."""
        mock_httpx_response = create_mock_httpx_response(500, text="Server Error")

        with patch("httpx.AsyncClient") as MockHttpxClient:
            mock_httpx = AsyncMock()
            mock_httpx.post = AsyncMock(return_value=mock_httpx_response)
            MockHttpxClient.return_value = mock_httpx

            with patch("openai.AsyncOpenAI") as MockOpenAI:
                mock_openai = MagicMock()
                mock_openai.chat.completions.create = AsyncMock(
                    side_effect=Exception("OpenAI also failed")
                )
                MockOpenAI.return_value = mock_openai

                with patch("app.services.llm_service.settings") as mock_settings:
                    mock_settings.OPENROUTER_API_KEY = "test-api-key"
                    mock_settings.OPENAI_API_KEY = "test-openai-key"
                    mock_settings.LLM_MODEL = "gpt-4"

                    service = LLMService(provider="cerebras")

                    with pytest.raises(LLMServiceError):
                        await service.generate(
                            messages=[{"role": "user", "content": "Hello"}],
                            fallback_on_error=True
                        )

    @pytest.mark.asyncio
    async def test_close_closes_all_clients(self):
        """Test that close() closes all initialized clients."""
        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=create_mock_httpx_response(200, create_success_response()))
            mock_client.aclose = AsyncMock()
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"

                service = LLMService(provider="cerebras")
                # Initialize client by making a request
                await service.generate(messages=[{"role": "user", "content": "Hello"}])

                await service.close()

        mock_client.aclose.assert_called()


# ========== Edge Cases ==========

class TestLLMServiceEdgeCases:
    """Edge case tests for LLM Service."""

    @pytest.mark.asyncio
    async def test_empty_messages(self):
        """Test handling of empty messages list."""
        mock_response = create_mock_httpx_response(200, create_success_response())

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")
                # Should not raise, API will handle empty messages
                response = await client.generate(messages=[])

        assert response is not None

    @pytest.mark.asyncio
    async def test_unicode_messages(self):
        """Test handling of unicode/non-ASCII messages."""
        mock_response = create_mock_httpx_response(
            200,
            create_success_response("Привет! Қалайсың? مرحبا")
        )

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")
                response = await client.generate(
                    messages=[{"role": "user", "content": "Қазақ тілінде сөйле"}]
                )

        assert "Привет" in response.content or "Қалайсың" in response.content

    @pytest.mark.asyncio
    async def test_response_without_usage_field(self):
        """Test handling of response without usage field."""
        mock_response = create_mock_httpx_response(
            200,
            {
                "choices": [
                    {
                        "message": {"content": "Response"},
                        "finish_reason": "stop"
                    }
                ]
                # No "usage" field
            }
        )

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")
                response = await client.generate(
                    messages=[{"role": "user", "content": "Hello"}]
                )

        assert response.tokens_used is None  # Should be None, not error

    @pytest.mark.asyncio
    async def test_very_long_content(self):
        """Test handling of very long content."""
        long_content = "A" * 10000  # 10K characters
        mock_response = create_mock_httpx_response(200, create_success_response(long_content))

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")
                response = await client.generate(
                    messages=[{"role": "user", "content": "Generate long text"}]
                )

        assert len(response.content) == 10000

    @pytest.mark.asyncio
    async def test_temperature_boundaries(self):
        """Test temperature parameter at boundaries."""
        mock_response = create_mock_httpx_response(200, create_success_response())

        with patch("httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with patch("app.services.llm_service.settings") as mock_settings:
                mock_settings.OPENROUTER_API_KEY = "test-api-key"
                mock_settings.OPENROUTER_BASE_URL = "https://api.test.com"
                mock_settings.CEREBRAS_MODEL = "test-model"

                client = OpenRouterClient(api_key="test-api-key")

                # Temperature 0 (deterministic)
                await client.generate(
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=0.0
                )

                # Temperature 2 (maximum)
                await client.generate(
                    messages=[{"role": "user", "content": "Hello"}],
                    temperature=2.0
                )

        assert mock_client.post.call_count == 2
