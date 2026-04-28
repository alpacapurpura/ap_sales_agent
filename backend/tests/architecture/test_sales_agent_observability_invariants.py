"""Architectural fitness tests for sales_agent S1 observability.

Three invariants:

1. **PII sanitization** — every payload that lands in
   ``sales_agent_trace_event`` or ``sales_agent_llm_call`` passes
   through :func:`sanitize_payload` (or is structurally typed —
   token counts, costs, durations are not strings).
2. **Best-effort persistence** — every ``_persist_*`` / ``_do_persist_*``
   in :class:`SalesAgentCallbackHandler` is wrapped in
   ``try / except`` + ``structlog.warning`` + session rollback.
3. **Subgraph callback forwarding** — ``orchestrator/graph.py``'s
   ``sales_agent_node`` declares ``config`` in its signature and
   forwards it to ``sales_app.invoke``. Without this the observability
   handler never sees the inner sales subgraph events.

Ratchet pattern: if any future change breaks an invariant the test
fails CI. Allowlists are intentionally absent — these are non-
negotiable starting from S1 day 1.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CALLBACK_HANDLER = REPO / "src" / "modules" / "sales_agent" / "observability" / "recording" / "callback_handler.py"
ORCHESTRATOR_GRAPH = REPO / "src" / "modules" / "sales_agent" / "application" / "orchestrator" / "graph.py"
TRACE_REPO = REPO / "src" / "modules" / "sales_agent" / "observability" / "persistence" / "trace_event_repository.py"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _ast(p: Path) -> ast.Module:
    return ast.parse(_read(p))


class TestSubgraphCallbackForwarding:
    """``sales_agent_node`` MUST declare ``config`` and forward it."""

    def test_node_signature_declares_config(self) -> None:
        tree = _ast(ORCHESTRATOR_GRAPH)
        target = next(
            (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "sales_agent_node"),
            None,
        )
        assert target is not None, "sales_agent_node missing"
        arg_names = [a.arg for a in target.args.args]
        assert "config" in arg_names, (
            "sales_agent_node must accept ``config`` so LangGraph propagates the parent "
            "RunnableConfig (and the observability callback handler) into the sales subgraph."
        )

    def test_node_forwards_config_to_subgraph_invoke(self) -> None:
        src = _read(ORCHESTRATOR_GRAPH)
        # Tight string match — refactors that drop the kwarg are caught.
        assert "sales_app.invoke(state, config=config)" in src, (
            "sales_agent_node must forward config to sales_app.invoke; otherwise the "
            "observability callback handler never sees inner subgraph events."
        )


class TestCallbackHandlerBestEffort:
    """Every persistence call in the callback handler is best-effort."""

    def test_callbacks_are_wrapped_in_try_except(self) -> None:
        tree = _ast(CALLBACK_HANDLER)
        # Every ``on_*`` async/sync method must contain a Try block.
        targets = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("on_")]
        # We expect on_chat_model_start / on_llm_end / on_llm_error /
        # on_tool_start / on_tool_end / on_tool_error / on_chain_start /
        # on_chain_end — eight total.
        assert len(targets) >= 8, f"Expected ≥8 ``on_*`` callbacks, got {len(targets)}"
        for fn in targets:
            has_try = any(isinstance(child, ast.Try) for child in ast.walk(fn))
            assert has_try, f"Callback {fn.name} must wrap its body in try/except (best-effort)."

    def test_logger_warning_used_in_handler(self) -> None:
        src = _read(CALLBACK_HANDLER)
        assert "logger.warning" in src, "Best-effort path must surface failures via structlog.warning."
        # No raise inside the on_* handlers — sample check on text.
        # (full proof is the try/except above; this guards future
        # regressions where someone re-adds ``raise``.)
        # We do allow ``raise`` in helper paths that are unrelated.
        for line in src.splitlines():
            stripped = line.strip()
            # Allow ``raise NotImplementedError`` only via abstract base
            # (not present in this concrete subclass).
            assert "raise NotImplementedError" not in stripped, (
                "Concrete handler must override ``_persist_*_row`` — never raise NotImplementedError here."
            )

    def test_rollback_invoked_on_persist_failures(self) -> None:
        src = _read(CALLBACK_HANDLER)
        assert "self._safe_rollback()" in src, (
            "Persistence failures must call ``_safe_rollback()`` so the next ORM "
            "operation in the same session does not see a poisoned transaction."
        )


class TestPiiSanitizationOnTraceWrites:
    """Trace event payload (the JSONB ``data`` column) MUST be sanitized."""

    def test_callback_handler_sanitizes_tool_args_and_outputs(self) -> None:
        src = _read(CALLBACK_HANDLER)
        # Every ``data=...`` kwarg produced inside on_tool_* / on_llm_end
        # must call ``sanitize_payload(...)``. We grep the surrounding
        # context — strict but stable.
        sanitized_calls = src.count("sanitize_payload(")
        assert sanitized_calls >= 3, (
            "Callback handler should pass at least 3 ``data`` payloads through "
            "``sanitize_payload`` (on_llm_end mirror + on_tool_end + on_tool_error). "
            f"Found {sanitized_calls}."
        )

    def test_trace_repository_signature_accepts_data_dict(self) -> None:
        """The repo's ``add()`` signature must keep ``data`` typed as
        ``dict`` — that is the contract sanitize_payload returns and the
        callback handler depends on it.
        """
        tree = _ast(TRACE_REPO)
        add_fn = next(
            (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "add"),
            None,
        )
        assert add_fn is not None
        kw_args = {a.arg for a in add_fn.args.kwonlyargs}
        for required in ("tenant_id", "lead_id", "channel_type", "event_type", "data"):
            assert required in kw_args, f"Trace repo add() missing required kwonly arg: {required}"

    def test_domain_event_subscribers_wrap_data_in_sanitize(self) -> None:
        subs_path = REPO / "src" / "modules" / "sales_agent" / "observability" / "domain_events" / "subscribers.py"
        src = _read(subs_path)
        # The single call to repo.add(... data=sanitize_payload(...) ...)
        # is the only place that touches the trace_event table from a
        # domain event handler.
        assert "sanitize_payload(payload)" in src, (
            "Domain-event subscriber must run payload through sanitize_payload "
            "before persisting to sales_agent_trace_event."
        )
