"""ContextWindowBuilder — walks messages backwards respecting token + msg caps.

See CONTRACT §2.3 and copilot-refactor-spec §2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from luana_core_copilot.application.memory.token_counter import count_tokens
from luana_core_copilot.domain.ports import LLMMessage

if TYPE_CHECKING:  # pragma: no cover
    from luana_core_copilot.domain.context_window import ContextWindowConfig


class ContextWindowBuilder:
    """Produces the raw-message window fed to the LLM.

    Walks ``messages`` newest→oldest, inserting into the window until either
    the token cap or message cap is hit. The ``RAW_WINDOW_MIN_MESSAGES``
    floor is always respected (included even if exceeding tokens — LLM can
    truncate defensively).
    """

    def __init__(self, config: ContextWindowConfig) -> None:
        """Store the config for build-time lookups."""
        self._cfg = config

    @classmethod
    def for_channel(cls, channel: str | None) -> ContextWindowBuilder:
        """Return a builder configured for ``channel`` (default web).

        PI-5 PR-2 (D-PI5-006): ``"telegram"`` selects the wider
        ``TELEGRAM_CONTEXT_WINDOW_CONFIG`` (3000 raw tokens, 15 msgs);
        any other value (including ``None``) falls back to
        ``DEFAULT_CONTEXT_WINDOW_CONFIG``. Existing call sites that
        construct ``ContextWindowBuilder(DEFAULT_CONTEXT_WINDOW_CONFIG)``
        keep working unchanged.
        """
        # Local import to avoid a cycle: domain → application is fine, but
        # the original module already imports ContextWindowConfig under
        # TYPE_CHECKING — keep the runtime import scoped here.
        from luana_core_copilot.domain.context_window import (
            get_context_window_config,
        )

        return cls(get_context_window_config(channel))

    def build(
        self,
        summary: str | None,
        messages: list[LLMMessage],
        new_user_msg: str,
    ) -> tuple[list[LLMMessage], int]:
        """Return (window, total_tokens) ready to be passed to the LLM.

        ``summary`` (when not None) is emitted as the first message in the
        window with role ``system`` and name ``rolling_summary``. The new
        user message is always appended last — it never counts toward the
        window cap but does count toward ``total_tokens``.
        """
        window: list[LLMMessage] = []
        tokens_used = 0

        if summary:
            summary_msg = LLMMessage(
                role="system",
                content=summary,
                name="rolling_summary",
            )
            window.append(summary_msg)
            tokens_used += count_tokens(summary)

        # Walk backwards so we keep the most recent messages when we hit caps.
        reversed_window: list[LLMMessage] = []
        reversed_tokens = 0
        for count, msg in enumerate(reversed(messages)):
            msg_tokens = count_tokens(msg.content)
            hit_token_cap = reversed_tokens + msg_tokens > self._cfg.RAW_WINDOW_TOKENS
            hit_msg_cap = count >= self._cfg.RAW_WINDOW_MAX_MESSAGES
            # Floor rule: always include at least RAW_WINDOW_MIN_MESSAGES.
            below_floor = count < self._cfg.RAW_WINDOW_MIN_MESSAGES
            if (hit_token_cap or hit_msg_cap) and not below_floor:
                break
            reversed_window.append(msg)
            reversed_tokens += msg_tokens

        reversed_window.reverse()
        window.extend(reversed_window)
        tokens_used += reversed_tokens

        # The new user message is appended last, outside the cap accounting.
        new_msg = LLMMessage(role="user", content=new_user_msg)
        window.append(new_msg)
        tokens_used += count_tokens(new_user_msg)

        return window, tokens_used
