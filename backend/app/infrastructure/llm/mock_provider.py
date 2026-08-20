"""Mock LLM provider for test and development environments.

Provides deterministic responses without requiring any external API key
or local model installation.  Used when ``LLM_PROVIDER=mock`` is set.

DO NOT use in production — this provider generates static SQL templates.
"""

from __future__ import annotations

import re

from app.application.interfaces.i_llm_provider import ILLMProvider, LLMResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class MockProvider(ILLMProvider):
    """Deterministic mock provider for dev/test environments.

    Parses the system prompt to extract the table name and generates
    a static ``SELECT * FROM <table> LIMIT 10`` query.  Returns zero
    cost and minimal token counts.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    def complete(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        _ = (user_message, max_tokens, temperature)  # interface compliance
        # Attempt to extract table name from schema context
        match = re.search(r'Table:\s*"([^"]+)"', system_prompt)
        table_name = match.group(1) if match else "data"

        sql = f'SELECT * FROM "{table_name}" LIMIT 10;'

        logger.debug(
            "MockProvider generating response",
            table=table_name,
            model=model,
        )

        return LLMResponse(
            content=sql,
            model=model or "mock-model",
            prompt_tokens=10,
            completion_tokens=10,
            total_tokens=20,
            cost_usd=0.0,
            provider="mock",
        )
