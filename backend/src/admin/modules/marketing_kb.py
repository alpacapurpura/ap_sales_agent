"""Streamlit admin module — curated marketing KB.

The KB is now globally curated by Nicolify staff (collection
``nicolify_marketing_kb``), so the admin page no longer surfaces
per-tenant ingestion. The four tabs are:

1. Vista general — collection stats + sources list.
2. Buscar — QA tool to preview retrieval results.
3. Cargar / actualizar — upload a markdown file (or paste content) and
   index with breadcrumb-aware chunking.
4. Reseed — trigger the canonical seed script over ``data/marketing_kb/``.

[COPILOT-MARKETING-KB-F10]
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
from luana_core_copilot.application.services.contextual_chunker import (
    ChunkingMeta,
    chunk_markdown,
)
from luana_core_copilot.infrastructure.qdrant.marketing_kb_store import (
    ALLOWED_CATEGORIES,
    ALLOWED_DOMAINS,
    ALLOWED_METHODOLOGIES,
    MarketingKbStore,
)


def get_store() -> MarketingKbStore:
    """Build a fresh store per render — lazy Qdrant connection."""
    return MarketingKbStore()


def _render_overview(store: MarketingKbStore) -> None:
    st.header("Vista general — Marketing KB curado")
    st.caption(
        "Colección global tenant-agnóstica. Esta KB la mantiene el staff de "
        "Nicolify; los tenants ya no pueden cargar documentos propios. "
        "Aquí ves el estado de la colección y qué documentos están indexados.",
    )

    try:
        stats: dict[str, Any] = store.stats()
        # B14-TP8 — qdrant-client 1.17 dropped ``vectors_count``. ``points_count``
        # is the canonical count (1 vector per point en dense single-vector setup).
        col1, col2, col3 = st.columns(3)
        col1.metric("Colección", stats.get("collection", "—"))
        col2.metric("Puntos", stats.get("points_count") or 0)
        col3.metric("Status", stats.get("status", "unknown"))
        if stats.get("error"):
            st.error(f"Error consultando Qdrant: {stats['error']}")
    except Exception as exc:  # noqa: BLE001 — Streamlit UI error boundary
        st.error(f"Error: {exc}")
        return

    st.divider()
    st.subheader("Documentos indexados")
    try:
        rows = store.list_sources(limit=500)
    except Exception as exc:  # noqa: BLE001 — Streamlit UI error boundary
        st.error(f"Error listando fuentes: {exc}")
        rows = []

    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.info(
            "Sin documentos indexados todavía. Usa la pestaña 'Recargar corpus' "
            "para correr el seeder canónico desde `backend/data/marketing_kb/`.",
        )


def _render_search(store: MarketingKbStore) -> None:
    st.header("Buscar (QA)")
    st.caption(
        "Probá una consulta tal como la haría el copilot. Útil para auditar "
        "que los chunks devueltos sean los correctos y bien etiquetados.",
    )

    query = st.text_input("Pregunta o tema a buscar", key="kb_query")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        domain = st.selectbox(
            "Dominio (opcional)",
            options=["(todos)", *sorted(ALLOWED_DOMAINS)],
            key="kb_domain",
        )
    with col_b:
        methodology = st.selectbox(
            "Metodología (opcional)",
            options=["(todas)", *sorted(ALLOWED_METHODOLOGIES)],
            key="kb_method",
        )
    with col_c:
        limit = st.slider("Resultados", 1, 10, 5, key="kb_limit")

    if st.button("Buscar", key="kb_search_btn") and query.strip():
        try:
            results = store.search(
                query,
                domain=None if domain == "(todos)" else domain,
                methodology=None if methodology == "(todas)" else methodology,
                limit=limit,
            )
        except Exception as exc:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {exc}")
            return

        if not results:
            st.info("Sin resultados.")
            return

        for idx, item in enumerate(results, start=1):
            with st.expander(
                f"#{idx} · score {item['score']:.3f} · "
                f"{item.get('methodology')} / {item.get('domain')} · "
                f"{item.get('source_doc')}",
            ):
                breadcrumb = " > ".join(item.get("breadcrumb") or [])
                if breadcrumb:
                    st.caption(f"Sección: {breadcrumb}")
                st.write((item.get("content") or "").strip())
                st.json(
                    {
                        "category": item.get("category"),
                        "tags": item.get("tags"),
                        "chunk_index": item.get("chunk_index"),
                    },
                )


def _render_upload(store: MarketingKbStore) -> None:
    st.header("Cargar o actualizar documento (manual)")
    st.caption(
        "Sube un markdown o pega contenido directo. El chunker breadcrumb-aware "
        "respeta encabezados (## / ###) como límites semánticos para preservar "
        "contexto de capítulo en cada chunk indexado.",
    )

    with st.form("kb_upload_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Categoría",
                options=sorted(ALLOWED_CATEGORIES),
                key="kb_up_category",
            )
            methodology = st.selectbox(
                "Metodología",
                options=sorted(ALLOWED_METHODOLOGIES),
                key="kb_up_method",
            )
            domain = st.selectbox(
                "Dominio",
                options=sorted(ALLOWED_DOMAINS),
                key="kb_up_domain",
            )
        with col2:
            source_doc = st.text_input(
                "Source doc (filename estable)",
                placeholder="ej. 31_nuevo_framework.md",
                key="kb_up_source",
            )
            tags_raw = st.text_input(
                "Tags separados por coma",
                key="kb_up_tags",
            )
            version = st.number_input("Versión", min_value=1, value=1, key="kb_up_ver")

        uploaded = st.file_uploader("Markdown (.md)", type=["md", "txt"], key="kb_up_file")
        pasted = st.text_area("…o pegá el contenido aquí", height=240, key="kb_up_paste")

        submitted = st.form_submit_button("Indexar")

        if submitted:
            content = ""
            if uploaded is not None:
                content = uploaded.read().decode("utf-8", errors="replace")
            elif pasted.strip():
                content = pasted

            if not content.strip():
                st.warning("Sin contenido — adjuntá un .md o pegá texto.")
                return
            if not source_doc.strip():
                st.warning("Indicá un source_doc estable (filename).")
                return

            try:
                meta = ChunkingMeta(
                    source_doc=source_doc.strip(),
                    category=category,
                    methodology=methodology,
                    domain=domain,
                    tags=tuple(t.strip() for t in tags_raw.split(",") if t.strip()),
                    version=int(version),
                )
                chunks = chunk_markdown(content, meta=meta)
                if not chunks:
                    st.warning("El chunker no produjo ningún chunk (¿documento muy chico?).")
                    return
                count = store.upsert_chunks(chunks)
                st.success(
                    f"✅ {count} chunks indexados para `{source_doc}`.",
                )
            except Exception as exc:  # noqa: BLE001 — Streamlit UI error boundary
                st.error(f"Error indexando: {exc}")

    st.divider()
    st.subheader("Eliminar todos los chunks de un source_doc")
    st.caption(
        "Útil cuando se reemplaza completamente un doc — primero eliminás, después subís la versión nueva.",
    )
    target = st.text_input(
        "source_doc a eliminar",
        key="kb_del_source",
        placeholder="ej. 02_hormozi_value_equation.md",
    )
    if st.button("🗑️ Eliminar", key="kb_del_btn") and target.strip():
        try:
            ok = store.delete_by_source_doc(target.strip())
            if ok:
                st.success("Eliminado.")
            else:
                st.error("No se pudo eliminar.")
        except Exception as exc:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {exc}")


def _render_reseed(store: MarketingKbStore) -> None:
    st.header("Recargar corpus desde `data/marketing_kb/`")
    st.caption(
        "Re-corre el seeder canónico sobre los `.md` versionados en repo. "
        "Idempotente: cada chunk tiene un id derivado de "
        "`source_doc + chunk_index + version`, así que reseed sobreescribe en su lugar.",
    )

    dry_run = st.checkbox(
        "Dry-run (sin tocar Qdrant)",
        value=True,
        key="kb_reseed_dry",
    )

    if st.button("Ejecutar seed", key="kb_reseed_btn"):
        try:
            from scripts.seed_nicolify_marketing_kb import seed

            per_doc = seed(dry_run=dry_run)
            if not per_doc:
                st.info("No se encontraron docs en `backend/data/marketing_kb/`.")
                return
            st.success(
                f"{'Dry-run' if dry_run else 'Seed'} OK — {sum(per_doc.values())} chunks en {len(per_doc)} docs.",
            )
            st.dataframe(
                pd.DataFrame(
                    [{"source_doc": k, "chunks": v} for k, v in sorted(per_doc.items())],
                ),
                hide_index=True,
                use_container_width=True,
            )
        except Exception as exc:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {exc}")


def render_marketing_kb_page() -> None:
    """Render the curated marketing KB admin page (4 tabs)."""
    st.title("📚 Marketing KB curado")
    st.markdown(
        "**Colección:** `nicolify_marketing_kb` · "
        "**Tenant-agnóstica** · "
        "**Curada por staff Nicolify** · "
        "**Embedding:** text-embedding-3-large (3072 dims) · "
        "**Chunking:** breadcrumb-aware (contextual retrieval, abril 2026).",
    )

    store = get_store()

    tab_overview, tab_search, tab_upload, tab_reseed = st.tabs(
        ["🌐 Vista general", "🔍 Buscar (QA)", "📥 Cargar / actualizar", "🔁 Recargar corpus"],
    )

    with tab_overview:
        _render_overview(store)
    with tab_search:
        _render_search(store)
    with tab_upload:
        _render_upload(store)
    with tab_reseed:
        _render_reseed(store)
