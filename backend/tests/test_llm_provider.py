"""Unit tests for LLM provider abstraction and failover service."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.interfaces.i_llm_provider import ILLMProvider, LLMResponse
from app.core.exceptions import AIProviderError
from app.core.logging import AuditLogger
from app.infrastructure.llm.provider_service import LLMProviderService


class DummyProvider(ILLMProvider):
    """Test double for LLM provider."""

    def __init__(self, name: str, should_fail: bool = False) -> None:
        self._name = name
        self.should_fail = should_fail
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def complete(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        _ = (system_prompt, user_message, max_tokens, temperature)
        self.call_count += 1
        if self.should_fail:
            raise AIProviderError(message=f"{self._name} simulated failure")

        return LLMResponse(
            content="SELECT * FROM users LIMIT 10;",
            model=model or "dummy-model",
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
            cost_usd=0.001,
            provider=self._name,
        )


def test_llm_response_dataclass() -> None:
    """Verify LLMResponse structure and default attributes."""
    res = LLMResponse(
        content="test",
        model="m1",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )
    assert res.content == "test"
    assert res.model == "m1"
    assert res.total_tokens == 15
    assert res.cost_usd is None
    assert res.provider == ""


def test_provider_service_primary_success() -> None:
    """Verify provider service uses primary provider when it succeeds."""
    primary = DummyProvider("primary")
    fallback = DummyProvider("fallback")
    audit = MagicMock(spec=AuditLogger)

    service = LLMProviderService(primary=primary, fallback=fallback, audit_logger=audit)
    response = service.complete(
        system_prompt="sys",
        user_message="user",
        user_id="usr_123",
    )

    assert response.content == "SELECT * FROM users LIMIT 10;"
    assert primary.call_count == 1
    assert fallback.call_count == 0
    audit.log_llm_transaction.assert_called_once()


def test_provider_service_failover_to_fallback() -> None:
    """Verify provider service falls back when primary fails."""
    primary = DummyProvider("primary", should_fail=True)
    fallback = DummyProvider("fallback")
    audit = MagicMock(spec=AuditLogger)

    service = LLMProviderService(primary=primary, fallback=fallback, audit_logger=audit)
    response = service.complete(
        system_prompt="sys",
        user_message="user",
        user_id="usr_123",
    )

    assert response.content == "SELECT * FROM users LIMIT 10;"
    assert primary.call_count == 1
    assert fallback.call_count == 1
    assert audit.log_llm_transaction.call_count == 2


def test_provider_service_all_fail_raises_exception() -> None:
    """Verify AIProviderError raised when all providers fail."""
    primary = DummyProvider("primary", should_fail=True)
    fallback = DummyProvider("fallback", should_fail=True)
    audit = MagicMock(spec=AuditLogger)

    service = LLMProviderService(primary=primary, fallback=fallback, audit_logger=audit)
    with pytest.raises(AIProviderError):
        service.complete(
            system_prompt="sys",
            user_message="user",
            user_id="usr_123",
        )

    assert primary.call_count == 1
    assert fallback.call_count == 1
