"""Process-wide accessor for the shared ARQ connection pool.

Rationale: FastAPI stores the pool on ``app.state.arq_pool`` — perfect for
handlers that receive ``Request`` but unreachable from LangChain tools which
run inside the orchestrator without a request object. This module exposes a
module-level singleton populated at app startup so tools can dispatch jobs
the same way endpoints do.

The pool itself is already a singleton (opened once at startup, closed at
shutdown); this just gives it an import site.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arq.connections import ArqRedis

_arq_pool: ArqRedis | None = None


def set_arq_pool(pool: ArqRedis | None) -> None:
    """Store the shared pool. Called from FastAPI startup/shutdown hooks."""
    global _arq_pool  # noqa: PLW0603 — module-level singleton
    _arq_pool = pool


def get_arq_pool() -> ArqRedis | None:
    """Return the shared pool, or ``None`` if ARQ is unavailable.

    Callers MUST handle ``None`` — Redis may be down, tests may skip it, or
    startup may have failed. Never assume a pool is connected.
    """
    return _arq_pool
