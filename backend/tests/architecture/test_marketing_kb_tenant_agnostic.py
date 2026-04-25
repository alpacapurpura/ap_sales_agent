"""Architecture fitness: ``MarketingKbStore`` is tenant-agnostic.

Curated marketing KB is GLOBAL: collection ``nicolify_marketing_kb`` carries
no per-tenant metadata, no per-tenant filter, no per-tenant ingestion path.

[COPILOT-MARKETING-KB-F10]
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STORE_PATH = REPO_ROOT / "src" / "modules" / "copilot" / "infrastructure" / "qdrant" / "marketing_kb_store.py"
TOOL_PATH = REPO_ROOT / "src" / "modules" / "copilot" / "application" / "tools" / "knowledge_search.py"


def _ast(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _identifiers_and_string_constants(path: Path) -> set[str]:
    """Collect all identifier names and string literals from real code (skip docstrings)."""
    tree = _ast(path)
    found: set[str] = set()

    # Drop module/class/function docstrings (first stmt if Constant str).
    def _strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            return body[1:]
        return body

    if isinstance(tree, ast.Module):
        tree.body = _strip_docstring(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            node.body = _strip_docstring(node.body)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.keyword) and node.arg:
            found.add(node.arg)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.add(node.value)
    return found


def test_store_module_does_not_reference_tenant_id() -> None:
    """``marketing_kb_store.py`` real code must not contain ``tenant_id``.

    Docstrings explaining the invariant are allowed; identifiers and string
    constants used in code are not.
    """
    tokens = _identifiers_and_string_constants(STORE_PATH)
    assert "tenant_id" not in tokens, (
        "MarketingKbStore must remain tenant-agnostic. "
        "Found 'tenant_id' identifier or literal in marketing_kb_store.py."
    )


def test_tool_module_does_not_reference_tenant_id() -> None:
    """``knowledge_search`` tool real code must not pass ``tenant_id`` anywhere."""
    tokens = _identifiers_and_string_constants(TOOL_PATH)
    assert "tenant_id" not in tokens, (
        "knowledge_search tool must remain tenant-agnostic. "
        "Found 'tenant_id' identifier or literal in knowledge_search.py."
    )


def test_store_collection_constant_is_global_name() -> None:
    """The collection constant must be the curated global one."""
    from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import (
        MARKETING_KB_COLLECTION,
        MarketingKbStore,
    )

    assert MARKETING_KB_COLLECTION == "nicolify_marketing_kb"
    assert MarketingKbStore.COLLECTION == "nicolify_marketing_kb"


def test_kb_chunk_payload_never_contains_tenant_id() -> None:
    """Defensive check: ``KbChunk.payload()`` cannot leak tenant identifiers."""
    from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import (
        KbChunk,
    )

    chunk = KbChunk(
        content="x" * 100,
        category="framework",
        methodology="hormozi",
        domain="offer",
        source_doc="test.md",
        chunk_index=0,
    )
    payload = chunk.payload()
    forbidden = {"tenant_id", "user_id", "tenant", "user"}
    assert forbidden.isdisjoint(payload.keys())


def test_vector_size_invariant() -> None:
    """Hardcoded 3072 dim — any embedder swap must be a deliberate breaking change."""
    from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import (
        MARKETING_KB_VECTOR_SIZE,
        MarketingKbStore,
    )

    assert MARKETING_KB_VECTOR_SIZE == 3072
    assert MarketingKbStore.VECTOR_SIZE == 3072


def test_store_search_signature_excludes_tenant_param() -> None:
    """``MarketingKbStore.search`` accepts no ``tenant_id`` keyword."""
    import inspect

    from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import (
        MarketingKbStore,
    )

    sig = inspect.signature(MarketingKbStore.search)
    assert "tenant_id" not in sig.parameters
    expected = {"self", "query", "domain", "methodology", "limit"}
    assert set(sig.parameters.keys()) == expected


def test_store_does_not_emit_tenant_id_field_condition() -> None:
    """AST sweep: no ``models.FieldCondition(key='tenant_id', ...)`` calls."""
    tree = _ast(STORE_PATH)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "key" and isinstance(kw.value, ast.Constant):
                assert kw.value.value != "tenant_id", "MarketingKbStore must not filter on tenant_id."
