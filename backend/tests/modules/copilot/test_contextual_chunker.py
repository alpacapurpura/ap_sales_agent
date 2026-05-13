"""Unit tests for ``contextual_chunker.chunk_markdown``."""

from __future__ import annotations

import textwrap

from luana_core_copilot.application.services.contextual_chunker import (
    ChunkingMeta,
    chunk_markdown,
)

_BASE_META = ChunkingMeta(
    source_doc="storybrand.md",
    category="framework",
    methodology="storybrand",
    domain="brand",
    tags=("hero-guide", "narrative"),
)


def test_chunker_empty_input_returns_empty_list() -> None:
    assert chunk_markdown("", meta=_BASE_META) == []
    assert chunk_markdown("   \n\n   ", meta=_BASE_META) == []


def test_chunker_emits_breadcrumb_per_heading() -> None:
    text = textwrap.dedent(
        """
        # StoryBrand

        Marco narrativo de Donald Miller que estructura la marca
        alrededor del cliente como héroe que necesita un guía. La idea
        principal: el cliente es protagonista, no la marca.

        ## El Hero

        El cliente carga con un problema externo y un anhelo interno
        que la marca debe entender antes de proponer la solución
        comercial. Desde ese ángulo nacen los mensajes del sitio.

        ### Internal Problem

        Conectar con el deseo profundo cierra ventas con menor fricción.

        ## El Guide

        La marca aparece con autoridad y empatía: muestra credenciales
        y demuestra que entiende el dolor. Sin esa entrada, no es la
        guía sino otra opción más en el mercado.
        """
    ).strip()

    chunks = chunk_markdown(text, meta=_BASE_META)
    assert chunks, "chunker emitted no chunks"

    breadcrumbs = [c.breadcrumb for c in chunks]
    assert ("StoryBrand",) in breadcrumbs
    assert ("StoryBrand", "El Hero") in breadcrumbs
    assert ("StoryBrand", "El Guide") in breadcrumbs


def test_chunker_propagates_meta_into_chunks() -> None:
    text = "# Tema\n\n" + ("Contenido relevante para el dominio de la oferta. " * 6)
    chunks = chunk_markdown(text, meta=_BASE_META)
    assert chunks
    for chunk in chunks:
        assert chunk.source_doc == _BASE_META.source_doc
        assert chunk.methodology == _BASE_META.methodology
        assert chunk.domain == _BASE_META.domain
        assert chunk.category == _BASE_META.category
        assert chunk.tags == _BASE_META.tags
        assert chunk.language == "es"
        assert chunk.version == 1


def test_chunker_drops_tiny_fragments() -> None:
    text = "# Tema\n\nok"  # too short, should be dropped (<80 chars)
    chunks = chunk_markdown(text, meta=_BASE_META)
    assert chunks == []


def test_chunker_strips_yaml_front_matter() -> None:
    text = textwrap.dedent(
        """
        ---
        title: Test
        forbidden_metadata: should_not_leak_into_embedding
        ---

        # Tema

        Cuerpo del documento que debe quedar después del front matter,
        suficientemente largo como para superar el umbral de 80 chars.
        """
    ).strip()
    chunks = chunk_markdown(text, meta=_BASE_META)
    assert chunks
    joined_content = " ".join(c.content for c in chunks)
    assert "forbidden_metadata" not in joined_content
    assert "title: Test" not in joined_content


def test_chunker_chunk_index_is_globally_enumerated() -> None:
    text = textwrap.dedent(
        """
        # Doc

        Sección uno con suficiente texto como para sobrevivir al umbral
        mínimo de tamaño que filtra fragmentos chicos.

        ## Sub uno

        Otra sección con texto distinto que debería generar un chunk
        independiente. Mantenemos esto largo y descriptivo.

        ## Sub dos

        Tercera sección igualmente sustancial para asegurar que
        producimos varios chunks dentro de un mismo documento.
        """
    ).strip()

    chunks = chunk_markdown(text, meta=_BASE_META)
    indices = [c.chunk_index for c in chunks]
    assert indices == sorted(indices)
    assert indices == list(range(len(chunks)))


def test_chunker_respects_chunk_size_for_long_section() -> None:
    long_paragraph = "Texto largo que debe partirse. " * 200  # ~6000 chars
    text = f"# Doc\n\n## Sección\n\n{long_paragraph}"

    chunks = chunk_markdown(text, meta=_BASE_META, chunk_tokens=128, overlap_tokens=32)
    assert len(chunks) >= 2  # got split
    for chunk in chunks:
        # 128 tokens * 4 chars/token = 512 cap (give some slack for splitter)
        assert len(chunk.content) <= 512 + 200
