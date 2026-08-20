"""LLM Provider port interface.

Defines the abstract contract for language model providers, enabling
swappable adapters (Anthropic, OpenAI) behind a uniform interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Structured response from an LLM provider call.

    Attributes
    ----------
    content : str
        The generated text response.
    model : str
        The model identifier that produced the response.
    prompt_tokens : int
        Number of tokens in the input prompt.
    completion_tokens : int
        Number of tokens in the generated response.
    total_tokens : int
        Total token usage (prompt + completion).
    cost_usd : float | None
        Estimated cost in USD, if calculable.
    provider : str
        The provider name (e.g., "anthropic", "openai").
    """

    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None
    provider: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


class ILLMProvider(ABC):
    """Port interface for language model providers.

    Implementations must handle their own HTTP transport, authentication,
    retries, and timeout enforcement. The caller receives a structured
    LLMResponse or raises an exception from the NexusBI error hierarchy.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical provider name (e.g., 'anthropic')."""

    @abstractmethod
    def complete(
        self,
        *,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Parameters
        ----------
        system_prompt : str
            The system-level instruction prompt.
        user_message : str
            The user's message content.
        model : str | None
            Optional model override. If None, use the provider's default.
        max_tokens : int
            Maximum tokens to generate.
        temperature : float
            Sampling temperature (0.0 = deterministic).

        Returns
        -------
        LLMResponse
            Structured response with content, token counts, and metadata.

        Raises
        ------
        AIProviderError
            If the provider returns a non-retryable error.
        AITimeoutError
            If the request exceeds the configured timeout.
        """
