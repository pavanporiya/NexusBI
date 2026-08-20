"""Ollama LLM provider adapter.

Implements ILLMProvider using the Ollama REST API for local model inference.
Supports any model available in the local Ollama instance (e.g. llama3.1,
codellama, mistral, deepseek-coder-v2, etc.).

Configuration via environment variables:
  LLM_PROVIDER=ollama
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=llama3.1
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.application.interfaces.i_llm_provider import ILLMProvider, LLMResponse
from app.core.exceptions import AIProviderError, AITimeoutError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Local Ollama models are free — cost is effectively zero.
_OLLAMA_COST_USD = 0.0


class OllamaProvider(ILLMProvider):
    """Ollama local model adapter implementing ILLMProvider.

    Uses the Ollama /api/chat endpoint with streaming disabled for
    synchronous response collection.

    Parameters
    ----------
    base_url : str
        Ollama server base URL (e.g. ``http://localhost:11434``).
    default_model : str
        Default model name to use when not specified per-call.
    timeout_seconds : int
        HTTP request timeout in seconds.
    """

    _CHAT_URL = "/api/chat"

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        default_model: str = "llama3.1",
        timeout_seconds: int = 120,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "ollama"

    def complete(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Send a completion request to the local Ollama API."""
        resolved_model = model or self._default_model

        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        url = f"{self._base_url}{self._CHAT_URL}"

        start = time.monotonic()
        last_error: Exception | None = None

        for attempt in range(1, 4):  # 3 attempts
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, json=payload)

                elapsed_ms = (time.monotonic() - start) * 1000

                if response.status_code == 200:
                    return self._parse_response(
                        response.json(), resolved_model, elapsed_ms
                    )

                if response.status_code in (500, 502, 503):
                    logger.warning(
                        "Ollama retryable error",
                        status_code=response.status_code,
                        attempt=attempt,
                        elapsed_ms=round(elapsed_ms, 2),
                    )
                    last_error = AIProviderError(
                        message=f"Ollama API returned {response.status_code}",
                        detail=response.text[:500],
                    )
                    continue

                raise AIProviderError(
                    message=f"Ollama API error (HTTP {response.status_code})",
                    detail=response.text[:500],
                )

            except httpx.TimeoutException:
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.warning(
                    "Ollama request timeout",
                    attempt=attempt,
                    timeout_seconds=self._timeout,
                    elapsed_ms=round(elapsed_ms, 2),
                )
                last_error = AITimeoutError(
                    provider="ollama",
                    timeout_seconds=self._timeout,
                )
                continue

            except httpx.HTTPError as exc:
                raise AIProviderError(
                    message="Ollama HTTP transport error",
                    detail=str(exc)[:500],
                ) from exc

        # All retries exhausted
        if isinstance(last_error, AITimeoutError):
            raise last_error
        raise last_error or AIProviderError(
            message="Ollama API failed after retries",
        )

    def _parse_response(
        self,
        data: dict[str, Any],
        model: str,
        elapsed_ms: float,  # noqa: ARG002
    ) -> LLMResponse:
        """Parse Ollama /api/chat response into LLMResponse."""
        message = data.get("message", {})
        content = message.get("content", "")

        # Ollama returns token counts in the response
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=_OLLAMA_COST_USD,
            provider="ollama",
            metadata={
                "total_duration_ns": data.get("total_duration"),
                "load_duration_ns": data.get("load_duration"),
                "prompt_eval_duration_ns": data.get("prompt_eval_duration"),
                "eval_duration_ns": data.get("eval_duration"),
            },
        )
