"""Seed the curated ``nicolify_marketing_kb`` Qdrant collection.

Reads every ``backend/data/marketing_kb/*.md`` file, parses YAML
front-matter for curation metadata, splits into breadcrumb-augmented
chunks, embeds with ``text-embedding-3-large`` (3072 dims) and upserts
to Qdrant. Idempotent: chunk ids are deterministic, so re-running
overwrites in place.

Usage:

    .venv/bin/python backend/scripts/seed_nicolify_marketing_kb.py
    .venv/bin/python backend/scripts/seed_nicolify_marketing_kb.py --dry-run
    .venv/bin/python backend/scripts/seed_nicolify_marketing_kb.py --only 02_hormozi_value_equation.md

[COPILOT-MARKETING-KB-F10]
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import structlog
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.modules.copilot.application.services.contextual_chunker import (
    ChunkingMeta,
    chunk_markdown,
)
from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import (
    ALLOWED_CATEGORIES,
    ALLOWED_DOMAINS,
    ALLOWED_METHODOLOGIES,
    KbChunk,
    MarketingKbStore,
)

logger = structlog.get_logger()

DATA_DIR = REPO_ROOT / "data" / "marketing_kb"
_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True, slots=True)
class CuratedDoc:
    """Parsed marketing KB document ready for chunking."""

    source_doc: str
    body: str
    meta: ChunkingMeta


def _parse_front_matter(text: str) -> dict[str, object]:
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return {}
    raw = match.group(1)
    parsed = yaml.safe_load(raw) or {}
    if not isinstance(parsed, dict):
        return {}
    return parsed


def _coerce_tags(value: object) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(v) for v in value)
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    return ()


def load_curated_docs(only: list[str] | None = None) -> list[CuratedDoc]:
    """Walk ``data/marketing_kb/`` and return parsed docs.

    ``only``: optional whitelist of filenames to limit which docs are seeded.
    Useful for incremental updates without reseeding the full corpus.
    """
    if not DATA_DIR.exists():
        msg = f"Marketing KB data dir missing: {DATA_DIR}"
        raise FileNotFoundError(msg)

    docs: list[CuratedDoc] = []
    for path in sorted(DATA_DIR.glob("*.md")):
        if only and path.name not in only:
            continue
        text = path.read_text(encoding="utf-8")
        front = _parse_front_matter(text)

        category = str(front.get("category", "framework"))
        methodology = str(front.get("methodology", "nicolify_owned"))
        domain = str(front.get("domain", "brand"))

        if category not in ALLOWED_CATEGORIES:
            msg = f"{path.name}: unknown category {category!r}"
            raise ValueError(msg)
        if methodology not in ALLOWED_METHODOLOGIES:
            msg = f"{path.name}: unknown methodology {methodology!r}"
            raise ValueError(msg)
        if domain not in ALLOWED_DOMAINS:
            msg = f"{path.name}: unknown domain {domain!r}"
            raise ValueError(msg)

        meta = ChunkingMeta(
            source_doc=path.name,
            category=category,
            methodology=methodology,
            domain=domain,
            tags=_coerce_tags(front.get("tags")),
            language=str(front.get("language", "es")),
            version=int(front.get("version", 1)),
        )
        docs.append(CuratedDoc(source_doc=path.name, body=text, meta=meta))
    return docs


def seed(
    *,
    dry_run: bool = False,
    only: list[str] | None = None,
    store: MarketingKbStore | None = None,
) -> dict[str, int]:
    """Run the seeding pipeline. Returns a dict ``source_doc -> chunks_indexed``."""
    docs = load_curated_docs(only=only)
    if not docs:
        return {}

    target = store if store is not None else MarketingKbStore()

    total_chunks: list[KbChunk] = []
    per_doc: dict[str, int] = {}
    for doc in docs:
        chunks = chunk_markdown(doc.body, meta=doc.meta)
        per_doc[doc.source_doc] = len(chunks)
        total_chunks.extend(chunks)

    if dry_run:
        logger.info(
            "marketing_kb_seed_dry_run",
            docs=len(docs),
            chunks=len(total_chunks),
            per_doc=per_doc,
        )
        return per_doc

    indexed = target.upsert_chunks(total_chunks)
    logger.info(
        "marketing_kb_seed_done",
        docs=len(docs),
        chunks=indexed,
        per_doc=per_doc,
    )
    return per_doc


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse + chunk without touching Qdrant.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Optional whitelist of *.md filenames to (re)seed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = seed(dry_run=args.dry_run, only=args.only)
    print(f"Docs procesados: {len(result)}")
    for source, count in sorted(result.items()):
        print(f"  {source}: {count} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
