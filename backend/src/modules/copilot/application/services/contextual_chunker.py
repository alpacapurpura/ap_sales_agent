"""Contextual chunker — breadcrumb-aware Markdown splitter.

State-of-art April 2026 contextual retrieval: each chunk preserves the
heading hierarchy (``# Doc > ## Section > ### Subsection``) as metadata
and the embed-time text prepends that breadcrumb so similarity search
keeps document context.

Chunk size: 512 tokens, overlap 100 (research-validated default).
Heading boundaries take priority over arbitrary character splits when
they fit within the size budget.

The chunker is *pure* — no I/O, no DB, no network. It accepts a markdown
string + ``source_doc`` filename + curation metadata and returns the
list of ``KbChunk`` ready for ``MarketingKbStore.upsert_chunks``.

[COPILOT-MARKETING-KB-F10]
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from luana_core_copilot.infrastructure.qdrant.marketing_kb_store import (
    KbChunk,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

# Token-to-char ratio (rough OpenAI tokenizer average for ES/EN markdown).
# 512 tokens ≈ 2048 chars at this ratio; 100 tokens ≈ 400 chars overlap.
_CHARS_PER_TOKEN = 4
DEFAULT_CHUNK_TOKENS = 512
DEFAULT_OVERLAP_TOKENS = 100

_HEADERS_TO_SPLIT = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
]

# Front-matter detection (--- at very top, --- closing). We strip it before
# chunking so YAML metadata never leaks into embeddings.
_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


@dataclass(frozen=True, slots=True)
class ChunkingMeta:
    """Curation metadata applied to every chunk produced from one source doc."""

    source_doc: str
    category: str
    methodology: str
    domain: str
    tags: tuple[str, ...] = ()
    language: str = "es"
    version: int = 1


def _build_breadcrumb(meta: dict[str, Any]) -> tuple[str, ...]:
    """Extract heading path from langchain's metadata dict."""
    crumbs: list[str] = []
    for key in ("h1", "h2", "h3", "h4"):
        value = meta.get(key)
        if value:
            crumbs.append(value.strip())
    return tuple(crumbs)


def _strip_front_matter(text: str) -> str:
    """Remove YAML front-matter so it never lands in embeddings."""
    return _FRONT_MATTER_RE.sub("", text, count=1).lstrip()


def chunk_markdown(
    markdown: str,
    *,
    meta: ChunkingMeta,
    chunk_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[KbChunk]:
    """Split ``markdown`` into breadcrumb-augmented chunks.

    Pipeline:

    1. Strip YAML front-matter.
    2. Split by markdown headings (``MarkdownHeaderTextSplitter``) so each
       leaf node carries an ``h1/h2/h3/h4`` breadcrumb.
    3. Recursively split oversized leaves with
       ``RecursiveCharacterTextSplitter`` (token-equivalent char budgets).
    4. Drop fragments under 80 chars (boilerplate noise).
    5. Emit ``KbChunk`` instances with ``chunk_index`` enumerated globally.

    Returns empty list for empty / whitespace-only inputs.
    """
    if not markdown.strip():
        return []

    cleaned = _strip_front_matter(markdown)

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADERS_TO_SPLIT,
        strip_headers=True,
    )
    docs = header_splitter.split_text(cleaned)

    chunk_chars = chunk_tokens * _CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * _CHARS_PER_TOKEN
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_chars,
        chunk_overlap=overlap_chars,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )

    chunks: list[KbChunk] = []
    chunk_index = 0
    for doc in docs:
        breadcrumb = _build_breadcrumb(doc.metadata or {})
        leaf_text = (doc.page_content or "").strip()
        if not leaf_text:
            continue

        if len(leaf_text) <= chunk_chars:
            pieces: Iterable[str] = [leaf_text]
        else:
            pieces = char_splitter.split_text(leaf_text)

        for raw_piece in pieces:
            piece = raw_piece.strip()
            if len(piece) < 80:
                continue
            chunks.append(
                KbChunk(
                    content=piece,
                    category=meta.category,
                    methodology=meta.methodology,
                    domain=meta.domain,
                    source_doc=meta.source_doc,
                    chunk_index=chunk_index,
                    breadcrumb=breadcrumb,
                    tags=meta.tags,
                    language=meta.language,
                    version=meta.version,
                )
            )
            chunk_index += 1

    return chunks
