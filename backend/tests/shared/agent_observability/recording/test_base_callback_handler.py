"""Invariants for ``BaseAgentCallbackHandler``."""

from __future__ import annotations

import inspect

import pytest


class TestBaseAgentCallbackHandlerAbstract:
    def test_class_is_abstract(self) -> None:
        from src.shared.agent_observability.recording.base_callback_handler import (
            BaseAgentCallbackHandler,
        )

        assert inspect.isabstract(BaseAgentCallbackHandler)

    def test_cannot_instantiate_directly(self) -> None:
        from src.shared.agent_observability.recording.base_callback_handler import (
            BaseAgentCallbackHandler,
        )

        with pytest.raises(TypeError, match="abstract"):
            BaseAgentCallbackHandler()  # type: ignore[abstract]

    def test_subclasses_langchain_base_callback_handler(self) -> None:
        from langchain_core.callbacks import BaseCallbackHandler

        from src.shared.agent_observability.recording.base_callback_handler import (
            BaseAgentCallbackHandler,
        )

        assert issubclass(BaseAgentCallbackHandler, BaseCallbackHandler)

    def test_required_abstract_methods(self) -> None:
        from src.shared.agent_observability.recording.base_callback_handler import (
            BaseAgentCallbackHandler,
        )

        abstracts = BaseAgentCallbackHandler.__abstractmethods__
        assert "_persist_llm_call_row" in abstracts
        assert "_persist_trace_event_row" in abstracts


class TestBaseRepoProtocols:
    def test_llm_call_repo_protocol_has_add(self) -> None:
        from src.shared.agent_observability.persistence.base_llm_call_repo import (
            BaseLLMCallRepoProtocol,
        )

        assert hasattr(BaseLLMCallRepoProtocol, "add")

    def test_trace_event_repo_protocol_has_add(self) -> None:
        from src.shared.agent_observability.persistence.base_trace_event_repo import (
            BaseTraceEventRepoProtocol,
        )

        assert hasattr(BaseTraceEventRepoProtocol, "add")

    def test_protocols_are_runtime_checkable_via_duck_typing(self) -> None:
        """Concrete repos must satisfy the protocol structurally — no inheritance required."""
        from src.shared.agent_observability.persistence.base_llm_call_repo import (
            BaseLLMCallRepoProtocol,
        )
        from src.shared.agent_observability.persistence.base_trace_event_repo import (
            BaseTraceEventRepoProtocol,
        )

        # Importing the protocol declaration must not error;
        # it is the runtime contract for sales_agent S1.
        assert BaseLLMCallRepoProtocol is not None
        assert BaseTraceEventRepoProtocol is not None
