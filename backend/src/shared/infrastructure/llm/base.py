"""Abstract base class for LLM provider implementations."""

from abc import ABC, abstractmethod
from typing import Any

from luana_core_platform.core.enums import ModelRole


class BaseLLMService(ABC):
    """Abstract base for LLM providers following the Strategy Pattern."""

    @abstractmethod
    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str = "smart",
        **kwargs: Any,  # noqa: ANN401 — abstract LLM interface
    ) -> str:
        """Generate a text response from the LLM.

        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}, ...]
            system_prompt: Optional system instruction to prepend or set.
            model_type: ModelRole enum or legacy string ("smart"/"fast").
            **kwargs: Extra parameters like temperature, max_tokens, etc.

        Returns:
            str: The generated text response.

        """

    @abstractmethod
    def get_embedding_model(self) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Return a LangChain-compatible embedding model object."""

    @abstractmethod
    def get_client(
        self,
        role: ModelRole = ModelRole.REASONING,
        *,
        temperature: float | None = None,
    ) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Return the underlying chat model client for the given role.

        Args:
            role: Model role (NANO/MINI/REASONING/HEAVY/AGENT).
            temperature: Optional override of the provider default temperature.
                Implementations MUST return a fresh ``BaseChatModel`` instance
                with the requested temperature baked in — they MUST NOT use
                ``Runnable.bind()`` to apply the override. ``deepagents 0.5+``
                rejects ``RunnableBinding`` in ``resolve_model`` (it is
                unhashable, and the harness profile cache uses dict lookup).
        """
