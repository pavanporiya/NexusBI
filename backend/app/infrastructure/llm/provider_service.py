"""LLM Provider Service with primary/fallback failover.

Orchestrates LLM calls through a primary provider with automatic
fallback to a secondary provider on failure. Integrates with the
AuditLogger for cost and token tracking.
"""

from __future__ import annotations

import time

from app.application.interfaces.i_llm_provider import ILLMProvider, LLMResponse
from app.core.exceptions import AIProviderError
from app.core.logging import AuditLogger, get_logger

logger = get_logger(__name__)


class LLMProviderService:
    """Failover-aware LLM provider orchestrator.

    Routes completion requests to the primary provider first. If the
    primary fails (timeout, error, etc.), transparently retries with
    the fallback provider. All transactions are logged via AuditLogger.

    Parameters
    ----------
    primary : ILLMProvider
        The preferred LLM provider (e.g., Anthropic Claude).
    fallback : ILLMProvider | None
        Optional fallback provider (e.g., OpenAI GPT-4o).
    audit_logger : AuditLogger
        Audit logger for recording LLM transactions.
    """

    def __init__(
        self,
        *,
        primary: ILLMProvider,
        fallback: ILLMProvider | None = None,
        audit_logger: AuditLogger,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._audit = audit_logger

    def complete(
        self,
        *,
        system_prompt: str,
        user_message: str,
        user_id: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Execute an LLM completion with failover and audit logging.

        Parameters
        ----------
        system_prompt : str
            System-level instruction prompt.
        user_message : str
            User's message content.
        user_id : str
            The authenticated user's ID for audit attribution.
        model : str | None
            Optional model override.
        max_tokens : int
            Maximum tokens to generate.
        temperature : float
            Sampling temperature.

        Returns
        -------
        LLMResponse
            The structured LLM response.

        Raises
        ------
        AIProviderError
            If both primary and fallback providers fail.
        """
        # Attempt primary provider
        start = time.monotonic()
        try:
            response = self._primary.complete(
                system_prompt=system_prompt,
                user_message=user_message,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            latency_ms = (time.monotonic() - start) * 1000
            self._log_transaction(
                user_id=user_id,
                response=response,
                latency_ms=latency_ms,
                status="success",
            )
            return response

        except Exception as primary_error:
            latency_ms = (time.monotonic() - start) * 1000
            logger.warning(
                "Primary LLM provider failed, attempting fallback",
                provider=self._primary.provider_name,
                error=str(primary_error)[:200],
                latency_ms=round(latency_ms, 2),
                has_fallback=self._fallback is not None,
            )

            self._log_transaction(
                user_id=user_id,
                response=None,
                latency_ms=latency_ms,
                status="error",
                _provider_name=self._primary.provider_name,
            )

            if self._fallback is None:
                raise

        # Attempt fallback provider
        start = time.monotonic()
        try:
            response = self._fallback.complete(
                system_prompt=system_prompt,
                user_message=user_message,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            latency_ms = (time.monotonic() - start) * 1000
            self._log_transaction(
                user_id=user_id,
                response=response,
                latency_ms=latency_ms,
                status="success",
                retry_count=1,
            )
            return response

        except Exception as fallback_error:
            latency_ms = (time.monotonic() - start) * 1000
            self._log_transaction(
                user_id=user_id,
                response=None,
                latency_ms=latency_ms,
                status="error",
                _provider_name=self._fallback.provider_name,
                retry_count=1,
            )
            raise AIProviderError(
                message="All LLM providers failed",
                detail=(
                    f"Primary ({self._primary.provider_name}) and fallback "
                    f"({self._fallback.provider_name}) both returned errors."
                ),
            ) from fallback_error

    def _log_transaction(
        self,
        *,
        user_id: str,
        response: LLMResponse | None,
        latency_ms: float,
        status: str,
        _provider_name: str | None = None,
        retry_count: int = 0,
    ) -> None:
        """Log an LLM transaction via the audit logger."""
        self._audit.log_llm_transaction(
            user_id=user_id,
            model=response.model if response else "unknown",
            prompt_tokens=response.prompt_tokens if response else 0,
            completion_tokens=response.completion_tokens if response else 0,
            latency_ms=latency_ms,
            cost_usd=response.cost_usd if response else None,
            status=status,
            retry_count=retry_count,
        )
