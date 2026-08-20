"""Tests for Ollama and Mock LLM providers.

All tests use mocked HTTP responses — no real Ollama installation required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import AIProviderError, AITimeoutError
from app.infrastructure.llm.mock_provider import MockProvider
from app.infrastructure.llm.ollama_provider import OllamaProvider

# ---------------------------------------------------------------------------
# MockProvider tests
# ---------------------------------------------------------------------------


class TestMockProvider:
    """Tests for the MockProvider dev/test adapter."""

    def test_provider_name(self) -> None:
        provider = MockProvider()
        assert provider.provider_name == "mock"

    def test_generates_select_query(self) -> None:
        provider = MockProvider()
        response = provider.complete(
            system_prompt='Table: "users"\nColumns:\n  - "id" (int)',
            user_message="Show me all users",
        )
        assert "SELECT" in response.content
        assert "users" in response.content
        assert response.provider == "mock"
        assert response.cost_usd == 0.0

    def test_extracts_table_name_from_schema(self) -> None:
        provider = MockProvider()
        response = provider.complete(
            system_prompt='Table: "sales_report"\nColumns:\n  - "revenue" (decimal)',
            user_message="Total revenue by month",
        )
        assert "sales_report" in response.content

    def test_fallback_table_name_when_no_match(self) -> None:
        provider = MockProvider()
        response = provider.complete(
            system_prompt="No table info here",
            user_message="Show data",
        )
        assert '"data"' in response.content

    def test_zero_tokens_and_cost(self) -> None:
        provider = MockProvider()
        response = provider.complete(system_prompt="", user_message="")
        assert response.total_tokens == 20
        assert response.cost_usd == 0.0


# ---------------------------------------------------------------------------
# OllamaProvider tests
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    """Tests for the Ollama provider with mocked HTTP."""

    def test_provider_name(self) -> None:
        provider = OllamaProvider()
        assert provider.provider_name == "ollama"

    def test_custom_config(self) -> None:
        provider = OllamaProvider(
            base_url="http://gpu-server:11434",
            default_model="codellama",
            timeout_seconds=60,
        )
        assert provider._base_url == "http://gpu-server:11434"
        assert provider._default_model == "codellama"
        assert provider._timeout == 60

    def test_strips_trailing_slash(self) -> None:
        provider = OllamaProvider(base_url="http://localhost:11434/")
        assert provider._base_url == "http://localhost:11434"

    def test_successful_completion(self) -> None:
        provider = OllamaProvider(base_url="http://localhost:11434")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3.1",
            "message": {
                "role": "assistant",
                "content": 'SELECT * FROM "users" LIMIT 10;',
            },
            "done": True,
            "total_duration": 1234567890,
            "load_duration": 123456,
            "prompt_eval_count": 50,
            "prompt_eval_duration": 234567,
            "eval_count": 15,
            "eval_duration": 345678,
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            response = provider.complete(
                system_prompt='Table: "users"\nColumns:\n  - "id" (int)',
                user_message="List all users",
            )

        assert response.content == 'SELECT * FROM "users" LIMIT 10;'
        assert response.model == "llama3.1"
        assert response.prompt_tokens == 50
        assert response.completion_tokens == 15
        assert response.total_tokens == 65
        assert response.provider == "ollama"
        assert response.cost_usd == 0.0

    def test_default_model_used_when_none_specified(self) -> None:
        provider = OllamaProvider(default_model="mistral")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "mistral",
            "message": {"content": "SELECT 1;"},
            "done": True,
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            response = provider.complete(system_prompt="test", user_message="test")

        assert response.model == "mistral"

    def test_custom_model_override(self) -> None:
        provider = OllamaProvider(default_model="llama3.1")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "deepseek-coder",
            "message": {"content": "SELECT 1;"},
            "done": True,
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            response = provider.complete(
                system_prompt="test",
                user_message="test",
                model="deepseek-coder",
            )

        assert response.model == "deepseek-coder"

    def test_retries_on_server_error(self) -> None:
        provider = OllamaProvider()

        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "model": "llama3.1",
            "message": {"content": "SELECT 1;"},
            "done": True,
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = [error_response, success_response]
            mock_client_cls.return_value = mock_client

            response = provider.complete(system_prompt="test", user_message="test")

        assert response.content == "SELECT 1;"

    def test_timeout_raises_ai_timeout_error(self) -> None:
        import httpx

        provider = OllamaProvider(timeout_seconds=5)

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.TimeoutException("timeout")
            mock_client_cls.return_value = mock_client

            with pytest.raises(AITimeoutError):
                provider.complete(system_prompt="test", user_message="test")

    def test_connection_error_raises_ai_provider_error(self) -> None:
        import httpx

        provider = OllamaProvider()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.ConnectError("refused")
            mock_client_cls.return_value = mock_client

            with pytest.raises(AIProviderError, match="transport"):
                provider.complete(system_prompt="test", user_message="test")

    def test_client_error_raises_ai_provider_error(self) -> None:
        provider = OllamaProvider()

        error_response = MagicMock()
        error_response.status_code = 400
        error_response.text = "Bad Request"

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = error_response
            mock_client_cls.return_value = mock_client

            with pytest.raises(AIProviderError, match="400"):
                provider.complete(system_prompt="test", user_message="test")

    def test_metadata_captured(self) -> None:
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3.1",
            "message": {"content": "SELECT 1;"},
            "done": True,
            "total_duration": 999999,
            "load_duration": 111111,
            "prompt_eval_duration": 222222,
            "eval_duration": 333333,
        }

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            response = provider.complete(system_prompt="test", user_message="test")

        assert response.metadata["total_duration_ns"] == 999999
        assert response.metadata["eval_duration_ns"] == 333333
