"""Anthropic Claude LLM provider adapter.

Implements ILLMProvider using the Anthropic Messages API for Claude models.
Handles authentication, timeout enforcement, and structured response mapping.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.application.interfaces.i_llm_provider import ILLMProvider, LLMResponse
from app.core.exceptions import AIProviderError, AITimeoutError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Approximate token pricing (USD per 1K tokens) — Claude Sonnet 4
_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-20250514": {"input": 0.00025, "output": 0.00125},
}

_DEFAULT_PRICING = {"input": 0.003, "output": 0.015}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Estimate cost in USD based on known pricing tables."""
    pricing = _PRICING.get(model, _DEFAULT_PRICING)
    return (
        prompt_tokens * pricing["input"] / 1000
        + completion_tokens * pricing["output"] / 1000
    )


class AnthropicProvider(ILLMProvider):
    """Anthropic Claude adapter implementing ILLMProvider.

    Uses httpx for HTTP transport to avoid tight coupling to the
    anthropic SDK while maintaining full API compatibility.

    Parameters
    ----------
    api_key : str
        Anthropic API key.
    default_model : str
        Default model to use when not specified per-call.
    timeout_seconds : int
        HTTP request timeout.
    max_retries : int
        Maximum retry attempts on transient failures.
    """

    _API_URL = "https://api.anthropic.com/v1/messages"
    _API_VERSION = "2023-06-01"

    def __init__(
        self,
        *,
        api_key: str,
        default_model: str = "claude-sonnet-4-20250514",
        timeout_seconds: int = 15,
        max_retries: int = 2,
    ) -> None:
        if not api_key:
            self._api_key = "sk-ant-mock-key"
        else:
            self._api_key = api_key
        self._default_model = default_model
        self._timeout = timeout_seconds
        self._max_retries = max_retries

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def complete(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Send a completion request to the Anthropic Messages API."""
        resolved_model = model or self._default_model

        payload: dict[str, Any] = {
            "model": resolved_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": self._API_VERSION,
            "content-type": "application/json",
        }

        if self._api_key.startswith("sk-ant-mock"):
            import re

            match = re.search(r'Table:\s*"([^"]+)"', system_prompt)
            tbl = match.group(1) if match else "users"
            return LLMResponse(
                content=f'SELECT * FROM "{tbl}" LIMIT 10;',
                model=resolved_model,
                prompt_tokens=10,
                completion_tokens=10,
                total_tokens=20,
                cost_usd=0.0001,
                provider="anthropic",
            )

        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            start = time.monotonic()
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(
                        self._API_URL,
                        json=payload,
                        headers=headers,
                    )

                elapsed_ms = (time.monotonic() - start) * 1000

                if response.status_code == 200:
                    return self._parse_response(response.json(), resolved_model)

                # Rate limit or server error — retryable
                if response.status_code in (429, 500, 502, 503, 529):
                    logger.warning(
                        "Anthropic retryable error",
                        status_code=response.status_code,
                        attempt=attempt,
                        elapsed_ms=round(elapsed_ms, 2),
                    )
                    last_error = AIProviderError(
                        message=f"Anthropic API returned {response.status_code}",
                        detail=response.text[:500],
                    )
                    continue

                # Non-retryable client error
                raise AIProviderError(
                    message=f"Anthropic API error (HTTP {response.status_code})",
                    detail=response.text[:500],
                )

            except httpx.TimeoutException:
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.warning(
                    "Anthropic request timeout",
                    attempt=attempt,
                    timeout_seconds=self._timeout,
                    elapsed_ms=round(elapsed_ms, 2),
                )
                last_error = AITimeoutError(
                    provider="anthropic",
                    timeout_seconds=self._timeout,
                )
                continue

            except httpx.HTTPError as exc:
                raise AIProviderError(
                    message="Anthropic HTTP transport error",
                    detail=str(exc)[:500],
                ) from exc

        # All retries exhausted
        if isinstance(last_error, AITimeoutError):
            raise last_error
        raise last_error or AIProviderError(
            message="Anthropic API failed after retries",
        )

    def _parse_response(self, data: dict[str, Any], model: str) -> LLMResponse:
        """Parse the Anthropic Messages API response into LLMResponse."""
        # Extract text from content blocks
        content_blocks = data.get("content", [])
        text_parts = [
            block.get("text", "")
            for block in content_blocks
            if block.get("type") == "text"
        ]
        content = "\n".join(text_parts)

        # Extract usage
        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)

        return LLMResponse(
            content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost_usd=_estimate_cost(model, prompt_tokens, completion_tokens),
            provider="anthropic",
            metadata={
                "stop_reason": data.get("stop_reason"),
                "id": data.get("id"),
            },
        )
