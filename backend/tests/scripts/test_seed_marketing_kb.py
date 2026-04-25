"""Tests for the marketing KB seeder script."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import (
        KbChunk,
    )


class _CapturingStore:
    """Captures upsert calls without touching Qdrant."""

    def __init__(self) -> None:
        self.calls: list[list[KbChunk]] = []

    def upsert_chunks(self, chunks: Any) -> int:
        chunks_list = list(chunks)
        self.calls.append(chunks_list)
        return len(chunks_list)


def test_seed_loads_all_curated_docs() -> None:
    """All 31 baseline docs in ``data/marketing_kb/`` should parse without error."""
    from scripts.seed_nicolify_marketing_kb import load_curated_docs

    docs = load_curated_docs()
    assert len(docs) >= 30, f"expected >=30 curated docs, got {len(docs)}"

    methodologies = {doc.meta.methodology for doc in docs}
    expected_subset = {
        "nicolify_owned",
        "storybrand",
        "hormozi",
        "cialdini",
        "aida",
        "pas",
        "jtbd",
        "fab",
        "4u",
    }
    assert expected_subset <= methodologies


def test_seed_dry_run_does_not_call_store() -> None:
    """``--dry-run`` should parse + chunk without touching the store."""
    from scripts.seed_nicolify_marketing_kb import seed

    store = _CapturingStore()
    per_doc = seed(dry_run=True, store=store)  # type: ignore[arg-type]

    assert store.calls == []
    assert per_doc, "dry run should still report per-doc chunk counts"
    assert all(count > 0 for count in per_doc.values())


def test_seed_real_run_upserts_chunks() -> None:
    from scripts.seed_nicolify_marketing_kb import seed

    store = _CapturingStore()
    per_doc = seed(only=["02_hormozi_value_equation.md"], store=store)  # type: ignore[arg-type]

    assert len(store.calls) == 1
    chunks = store.calls[0]
    assert chunks
    assert all(c.source_doc == "02_hormozi_value_equation.md" for c in chunks)
    assert per_doc == {"02_hormozi_value_equation.md": len(chunks)}


def test_seed_chunks_carry_breadcrumb() -> None:
    from scripts.seed_nicolify_marketing_kb import seed

    store = _CapturingStore()
    seed(only=["01_storybrand_framework.md"], store=store)  # type: ignore[arg-type]
    chunks = store.calls[0]

    breadcrumbs = {c.breadcrumb for c in chunks}
    assert any("StoryBrand" in cb[0] if cb else False for cb in breadcrumbs)


def test_seed_idempotent_chunk_ids() -> None:
    """Running the seeder twice produces the same chunk ids (idempotent)."""
    from scripts.seed_nicolify_marketing_kb import seed

    store_a = _CapturingStore()
    store_b = _CapturingStore()
    seed(only=["02_hormozi_value_equation.md"], store=store_a)  # type: ignore[arg-type]
    seed(only=["02_hormozi_value_equation.md"], store=store_b)  # type: ignore[arg-type]

    ids_a = sorted(c.stable_id() for c in store_a.calls[0])
    ids_b = sorted(c.stable_id() for c in store_b.calls[0])
    assert ids_a == ids_b
