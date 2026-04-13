"""Streamlit admin module for Copilot Knowledge Base monitoring."""

import pandas as pd
import streamlit as st

from src.admin.modules._shared import get_tenant_name, render_tenant_selector
from src.modules.copilot.application.services.knowledge_ingestion import (
    KnowledgeIngestionService,
)
from src.modules.copilot.infrastructure.knowledge.vector_store import (
    CopilotKnowledgeStore,
)


def get_store() -> CopilotKnowledgeStore:
    """Create a new knowledge store instance."""
    return CopilotKnowledgeStore()


def render_knowledge_page() -> None:
    """Render the copilot knowledge base management page."""
    st.title("🧠 Knowledge Base — Copilot")

    # ── Guia contextual permanente ──
    with st.expander("📖 ¿Que es el Knowledge Base y para que sirve?", expanded=False):
        st.markdown("""
**El Knowledge Base es la memoria a largo plazo del Copilot.** Sin el, el copilot solo sabe
lo que esta en los formularios (brand, offer, etc.). Con el, el copilot puede responder
preguntas usando **documentos reales del negocio** del tenant — manuales, FAQs, guias, catalogos.

**Scopes (alcances):**
- **`help`** — Documentacion de como usar Nicolify. Ayuda al usuario a configurar la plataforma.
- **`business`** — Documentacion del negocio del tenant. Ayuda al copilot a dar
  respuestas informadas sobre el producto/servicio del cliente.

**Flujo tipico como admin:**
1. **Vista General** → "¿Que tenants no tienen knowledge?" → Detectar huecos
2. **Ingestar** → Subir FAQ/catalogo del tenant, o generar auto-resumen
3. **Buscar** → Probar que las respuestas del copilot son buenas (herramienta de QA)
4. **Explorar** → Auditar periodicamente que no haya docs viejos
5. **Eliminar** → Limpiar lo obsoleto

**El resultado:** Un copilot que no solo ayuda a configurar la plataforma, sino que
**conoce el negocio de cada cliente** y puede dar respuestas contextuales e informadas.
""")

    tab_overview, tab_dashboard, tab_explore, tab_search, tab_ingest, tab_delete = st.tabs(
        [
            "🌐 Vista General",
            "📊 Dashboard",
            "📋 Explorar Documentos",
            "🔍 Buscar",
            "📥 Ingestar Docs",
            "🗑️ Eliminar",
        ],
    )

    # --- TAB 0: Vista General ---
    with tab_overview:
        st.header("Vista General Cross-Tenant")
        st.info(
            "**Para que sirve:** Ver de un vistazo que tenants tienen documentos indexados y cuales no. "
            "Si un tenant tiene chunks en `help` pero 0 en `business`, su copilot puede ayudarle a usar "
            "la plataforma pero NO tiene contexto de su negocio — considera ingestar info de su producto.",
        )
        try:
            store = get_store()
            all_docs = store.list_documents(limit=500)
            if all_docs:
                # Group by tenant + scope
                from collections import defaultdict

                groups = defaultdict(lambda: {"docs": set(), "chunks": 0, "last": None})
                for doc in all_docs:
                    key = (doc.get("tenant_id", "?"), doc.get("scope", "?"))
                    groups[key]["docs"].add(doc.get("document_id", doc.get("id", "")))
                    groups[key]["chunks"] += 1

                rows = []
                for (tid, scope), info in sorted(groups.items()):
                    rows.append(
                        {
                            "Tenant": get_tenant_name(tid),
                            "Scope": scope,
                            "Documentos": len(info["docs"]),
                            "Chunks": info["chunks"],
                        },
                    )

                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                )
                st.caption(f"Total: {len(all_docs)} chunks")
            else:
                st.info("No hay documentos indexados.")
        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error: {e}")

    # --- TAB 1: Dashboard ---
    with tab_dashboard:
        st.header("Stats de Colección")
        st.caption(
            "Health check tecnico: verifica que Qdrant (motor de busqueda vectorial)"
            " esta funcionando y cuantos vectores hay.",
        )
        try:
            store = get_store()
            stats = store.get_collection_stats()
            col1, col2, col3 = st.columns(3)
            col1.metric("Colección", stats.get("collection", "—"))
            col2.metric("Vectores", stats.get("vectors_count", 0))
            col3.metric("Puntos", stats.get("points_count", 0))

            if stats.get("error"):
                st.error(f"Error: {stats['error']}")
            else:
                st.success(f"Status: {stats.get('status', 'unknown')}")
        except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
            st.error(f"Error conectando a Qdrant: {e}")

    # --- TAB 2: Explorar Documentos ---
    with tab_explore:
        st.header("Explorar Documentos")
        st.caption(
            "Audita que documentos concretos estan indexados por tenant y scope. "
            "Util para detectar info desactualizada (ej: precios viejos) que deberia eliminarse y re-ingestarse.",
        )

        col1, col2 = st.columns(2)
        with col1:
            explore_tid = render_tenant_selector(
                key="kb_explore_tenant",
                allow_all=True,
            )
            tenant_filter = str(explore_tid) if explore_tid else None
        with col2:
            scope_filter = st.selectbox(
                "Scope",
                ["all", "help", "business"],
                key="explore_scope",
            )

        explore_limit = st.slider("Límite", 10, 500, 100, key="explore_limit")

        if st.button("Cargar Documentos", key="explore_btn"):
            try:
                store = get_store()
                docs = store.list_documents(
                    tenant_id=tenant_filter or None,
                    scope=scope_filter if scope_filter != "all" else None,
                    limit=explore_limit,
                )
                if docs:
                    df = pd.DataFrame(docs)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.caption(f"Mostrando {len(docs)} documentos")
                else:
                    st.info("No se encontraron documentos.")
            except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
                st.error(f"Error: {e}")

    # --- TAB 3: Buscar ---
    with tab_search:
        st.header("Buscar en Knowledge Base")
        st.caption(
            "Herramienta de QA: prueba exactamente lo que haria el copilot cuando un usuario pregunta algo. "
            "Escribe una pregunta real y verifica que los chunks devueltos sean relevantes y con buen score.",
        )

        search_query = st.text_input("Query de búsqueda", key="search_query")
        col1, col2 = st.columns(2)
        with col1:
            search_tid = render_tenant_selector(key="kb_search_tenant", allow_all=False)
            search_tenant = str(search_tid) if search_tid else ""
        with col2:
            search_scope = st.selectbox(
                "Scope",
                ["all", "help", "business"],
                key="search_scope",
            )

        if st.button("Buscar", key="search_btn") and search_query and search_tenant:
            try:
                store = get_store()
                results = store.search(
                    query=search_query,
                    tenant_id=search_tenant,
                    scope=search_scope if search_scope != "all" else None,
                    limit=5,
                )
                if results:
                    for i, r in enumerate(results):
                        score = r.get("score", 0)
                        text = r.get("text", "")[:300]
                        meta = r.get("meta", {})
                        source = meta.get("source", "—")
                        scope_val = meta.get("scope", "—")

                        with st.expander(
                            f"#{i + 1} — Score: {score:.4f} | {source} ({scope_val})",
                        ):
                            st.write(text)
                            st.json(meta)
                else:
                    st.info("Sin resultados.")
            except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
                st.error(f"Error: {e}")

    # --- TAB 4: Ingestar ---
    with tab_ingest:
        st.header("Ingestar Documentos")
        st.info(
            "**Aqui alimentas la memoria del copilot.** Dos modos:\n"
            "- **Subir Archivo** — PDF/DOCX/TXT con info del negocio del tenant (FAQ, catalogo, precios, manual)\n"
            "- **Auto-Resumen** — Genera automaticamente un doc a partir de lo que el tenant"
            " ya configuro (brand + offers). "
            "Quick-start para que el copilot tenga contexto sin subir nada manual.\n\n"
            "**Scope `help`** = como usar Nicolify. **Scope `business`** = info del negocio del cliente.",
        )

        st.subheader("📄 Subir Archivo")
        with st.form("ingest_form", clear_on_submit=True):
            ingest_tid = render_tenant_selector(key="kb_ingest_tenant", allow_all=False)
            ingest_tenant = str(ingest_tid) if ingest_tid else ""
            ingest_scope = st.selectbox(
                "Scope",
                ["help", "business"],
                key="ingest_scope",
            )
            ingest_source = st.text_input(
                "Source Label",
                value="upload",
                key="ingest_source",
            )
            uploaded_file = st.file_uploader(
                "Archivo (PDF/DOCX/TXT/MD)",
                type=["pdf", "docx", "txt", "md"],
            )

            submitted = st.form_submit_button("Ingestar")
            if submitted and uploaded_file and ingest_tenant:
                try:
                    # Read file content
                    content_bytes = uploaded_file.read()
                    filename = uploaded_file.name.lower()

                    if filename.endswith(".pdf"):
                        from src.shared.infrastructure.files.file_parsing_service import (
                            FileParsingService,
                        )

                        text = FileParsingService.parse_pdf(content_bytes)
                    elif filename.endswith(".docx"):
                        from src.shared.infrastructure.files.file_parsing_service import (
                            FileParsingService,
                        )

                        text = FileParsingService.parse_docx(content_bytes)
                    else:
                        try:
                            text = content_bytes.decode("utf-8")
                        except UnicodeDecodeError:
                            text = content_bytes.decode("latin-1")

                    if text.strip():
                        service = KnowledgeIngestionService()
                        result = service.ingest_document(
                            tenant_id=ingest_tenant,
                            content=text,
                            source=ingest_source,
                            scope=ingest_scope,
                        )
                        st.success(
                            f"✅ Documento ingestado! ID: {result['document_id']}, Chunks: {result['chunks_indexed']}",
                        )
                    else:
                        st.warning("No se pudo extraer texto del archivo.")
                except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
                    st.error(f"Error: {e}")

        st.divider()

        st.subheader("🤖 Auto-Resumen de Producto")
        auto_tid = render_tenant_selector(key="kb_auto_tenant", allow_all=False)
        auto_tenant = str(auto_tid) if auto_tid else ""
        if st.button("Generar Auto-Resumen", key="auto_summary_btn") and auto_tenant:
            try:
                service = KnowledgeIngestionService()
                result = service.ingest_product_summary(auto_tenant)
                if result["chunks_indexed"] > 0:
                    st.success(
                        f"✅ Auto-resumen generado! ID: {result['document_id']}, Chunks: {result['chunks_indexed']}",
                    )
                else:
                    st.warning(
                        "No se encontraron datos del tenant para generar resumen.",
                    )
            except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
                st.error(f"Error: {e}")

    # --- TAB 5: Eliminar ---
    with tab_delete:
        st.header("Eliminar Documentos")
        st.caption(
            "Quita documentos obsoletos o incorrectos. Si el copilot esta dando info vieja o equivocada, "
            "elimina el documento aqui y re-ingesta la version correcta en la tab Ingestar.",
        )
        st.warning("⚠️ Esta accion es irreversible.")

        del_tid = render_tenant_selector(key="kb_del_tenant", allow_all=False)
        del_tenant = str(del_tid) if del_tid else ""
        del_doc_id = st.text_input("Document ID", key="del_doc_id")

        if st.button("🗑️ Eliminar", key="del_btn") and del_tenant and del_doc_id:
            confirm = st.checkbox(
                "Confirmo que quiero eliminar este documento",
                key="del_confirm",
            )
            if confirm:
                try:
                    service = KnowledgeIngestionService()
                    deleted = service.delete_document(del_tenant, del_doc_id)
                    if deleted:
                        st.success("Documento eliminado.")
                    else:
                        st.error("Error eliminando documento.")
                except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
                    st.error(f"Error: {e}")
