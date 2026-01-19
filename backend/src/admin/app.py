import streamlit as st
import os
import sys
import time
import pandas as pd
from sqlalchemy import select, desc

# Add project root to path to import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config import settings
from src.services.database import SessionLocal
from src.services.db.repositories.audit import AuditRepository
from src.services.db.models.observability import AgentTrace, Message
from src.services.db.models.business import PromptVersion, SensitiveData
from src.services.knowledge_service import KnowledgeService

# Initialize Service
kb_service = KnowledgeService()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Visionarias Brain Admin",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- VIEWS FUNCTIONS ---

def render_safety_layer_manager():
    st.title("🛡️ Gestión de Datos Sensibles (Safety Layer)")
    st.markdown("""
    Configura las reglas de censura y reemplazo para proteger información crítica.
    El sistema aplica estas reglas en el último paso antes de responder al usuario.
    """)
    
    db = SessionLocal()
    
    # --- ADD NEW RULE ---
    with st.expander("➕ Agregar Nueva Regla", expanded=False):
        with st.form("add_sensitive_rule"):
            col1, col2 = st.columns(2)
            with col1:
                pattern = st.text_input("Patrón (Regex o Palabra Clave)", help="Ej: `\d{4}-\d{4}` o `CLAVE_SECRETA`")
                replacement = st.text_input("Reemplazo", value="[REDACTED]", help="Texto que verá el usuario")
            with col2:
                category = st.selectbox("Categoría", ["financial", "pii", "business_secret", "system_prompt"])
                description = st.text_input("Descripción (Opcional)")
            
            context_instruction = st.text_area(
                "Instrucción de Contexto (Opcional - Activa LLM Check)", 
                help="Si se llena, un LLM verificará el contexto antes de censurar. Ej: 'Solo censurar si se refiere a la clave maestra, no a claves musicales'."
            )
            
            if st.form_submit_button("Guardar Regla"):
                if pattern and replacement:
                    new_rule = SensitiveData(
                        pattern=pattern,
                        replacement=replacement,
                        category=category,
                        description=description,
                        context_instruction=context_instruction if context_instruction.strip() else None
                    )
                    db.add(new_rule)
                    db.commit()
                    st.success("Regla agregada exitosamente.")
                    st.rerun()
                else:
                    st.error("Patrón y Reemplazo son obligatorios.")

    # --- LIST RULES ---
    st.divider()
    st.subheader("📋 Reglas Activas")
    
    rules = db.query(SensitiveData).order_by(SensitiveData.created_at.desc()).all()
    
    if not rules:
        st.info("No hay reglas definidas.")
    else:
        for rule in rules:
            with st.expander(f"{'🟢' if rule.is_active else '🔴'} {rule.pattern} -> {rule.replacement} ({rule.category})"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**Descripción:** {rule.description or '-'}")
                    if rule.context_instruction:
                        st.info(f"🤖 **Verificación LLM Activa:** {rule.context_instruction}")
                with c2:
                    if st.button("Alternar Estado", key=f"toggle_{rule.id}"):
                        rule.is_active = not rule.is_active
                        db.commit()
                        st.rerun()
                    
                    if st.button("🗑️ Eliminar", key=f"del_{rule.id}", type="primary"):
                        db.delete(rule)
                        db.commit()
                        st.rerun()
    
    db.close()

def render_dashboard():
    st.title("🏠 Dashboard")
    st.markdown("### Estado del Sistema")
    
    stats = kb_service.get_system_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if stats["qdrant_connected"]:
            st.metric("Vectores Totales (Qdrant)", stats["vector_count"])
        else:
            st.error("Qdrant desconectado")

    with col2:
        if stats["doc_count"] != -1:
            st.metric("Documentos Indexados", stats["doc_count"])
        else:
            st.metric("Documentos Indexados", "Error DB")

    with col3:
        st.metric("Modelo LLM Activo", stats["llm_model"])

    st.divider()
    st.info("Bienvenido al panel de administración del Cerebro de Visionarias. Usa el menú lateral para navegar.")

def render_upload_view():
    st.title("📤 Cargar Documentos")
    st.markdown("Sube y procesa documentos para la base de conocimiento.")
    
    valid_categories = kb_service.get_valid_categories()
    
    with st.container(border=True):
        col_conf1, col_conf2 = st.columns(2)
        
        with col_conf1:
            st.subheader("1. Categorización")
            doc_categories = st.multiselect(
                "Etiquetas de Contenido",
                valid_categories,
                default=["product_logic"],
                help="Define qué tipo de información contiene este documento."
            )
            with st.expander("ℹ️ Ver Guía de Categorías"):
                st.markdown("""
                - **protocol_boundary**: Reglas inquebrantables. Filtros, puntualidad, cámara encendida.
                - **sales_persuasion**: Scripts de objeciones, re-encuadres, scripts de venta.
                - **financial_legal**: Precios, facturación, garantías, contratos, reembolsos.
                - **product_logic**: Fechas, horarios, temario, plataforma, entregables.
                - **avatar_psychology**: Dolores, deseos, identidad del cliente, diagnóstico emocional.
                - **brand_authority**: Historias de Camila/Ileana, filosofía, diferenciación.
                """)

        with col_conf2:
            st.subheader("2. Estrategia de Procesamiento")
            chunking_strategy = st.radio(
                "Modo de Fragmentación (Chunking)",
                ["Básico (Rápido)", "Avanzado (Semántico + Contexto IA)"],
                index=1,
                help="El modo avanzado usa IA para entender el contexto global antes de cortar el texto."
            )

    uploaded_file = st.file_uploader("Seleccionar archivo (PDF, TXT, MD)", type=['pdf', 'txt', 'md'])

    if uploaded_file:
        # File Size Check
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 5 and "Avanzado" in chunking_strategy:
            st.warning(f"⚠️ Archivo grande ({file_size_mb:.1f} MB). El modo 'Avanzado' puede tardar mucho. Si falla, usa 'Básico'.")

        if st.button("🚀 Procesar e Indexar", type="primary", use_container_width=True):
            with st.status("Iniciando procesamiento...", expanded=True) as status:
                try:
                    # Define callback to update UI
                    def update_progress(msg):
                        status.write(msg)
                        
                    kb_service.ingest_file(
                        filename=uploaded_file.name,
                        file_content=uploaded_file.getvalue(),
                        categories=doc_categories,
                        strategy=chunking_strategy,
                        on_progress=update_progress
                    )
                    
                    status.update(label="✅ Procesamiento completado", state="complete", expanded=False)
                    st.success(f"✅ Archivo '{uploaded_file.name}' indexado correctamente.")
                    
                except Exception as e:
                    status.update(label="❌ Error", state="error", expanded=True)
                    st.error(f"Error procesando archivo: {e}")

def render_bulk_upload_view():
    st.title("📚 Carga Masiva (Avanzado)")
    st.markdown("Sube múltiples documentos. La IA clasificará y fragmentará automáticamente.")
    
    with st.expander("ℹ️ Cómo funciona", expanded=True):
        st.info("""
        1. **Sube tus archivos** (PDF, TXT, MD).
        2. El sistema **leerá el contenido** de cada uno.
        3. Un LLM **detectará automáticamente la categoría** (Ej: Precios -> financial_legal).
        4. Se aplicará **Chunking Semántico (Avanzado)** por defecto.
        """)

    uploaded_files = st.file_uploader(
        "Seleccionar archivos (Múltiples)", 
        type=['pdf', 'txt', 'md'],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.write(f"📂 {len(uploaded_files)} archivos seleccionados.")
        
        if st.button("🚀 Procesar Lote", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            processed_count = 0
            errors = []
            
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    status_text.write(f"🔄 Procesando {i+1}/{len(uploaded_files)}: **{uploaded_file.name}**...")
                    
                    # 1. Preview & Classify
                    file_content = uploaded_file.getvalue()
                    preview_text = kb_service.extract_preview(uploaded_file.name, file_content)
                    suggested_category = kb_service.classify_preview(preview_text)
                    
                    st.toast(f"🤖 {uploaded_file.name} -> **{suggested_category}**")
                    
                    # 2. Process
                    with st.expander(f"✅ {uploaded_file.name} ({suggested_category})"):
                         kb_service.ingest_file(
                            filename=uploaded_file.name,
                            file_content=file_content,
                            categories=[suggested_category],
                            strategy="Avanzado (Semántico + Contexto IA)",
                            on_progress=st.write # Simple write to expander
                        )
                    
                    processed_count += 1
                    
                except Exception as e:
                    errors.append(f"{uploaded_file.name}: {str(e)}")
                    st.error(f"❌ Error en {uploaded_file.name}: {e}")
                
                # Update progress
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_text.write("✨ ¡Carga masiva completada!")
            
            if errors:
                st.warning(f"Se completaron {processed_count} archivos con {len(errors)} errores.")
                with st.expander("Ver Errores"):
                    for err in errors:
                        st.write(err)
            else:
                st.balloons()
                st.success(f"Se procesaron {processed_count} documentos exitosamente.")

def render_inventory_view():
    st.title("📂 Inventario de Documentos")
    
    col_act1, col_act2 = st.columns([4, 1])
    with col_act2:
        if st.button("🔄 Refrescar"):
            st.rerun()

    documents = kb_service.list_documents()
    
    if not documents:
        st.info("No hay documentos en el sistema.")
        return

    # Dataframe prep
    data = []
    valid_categories = kb_service.get_valid_categories()

    for doc in documents:
        current_cats = doc.category.split(",") if doc.category else []
        current_cats = [c for c in current_cats if c] # Filter empty

        data.append({
            "ID": str(doc.id),
            "Archivo": doc.filename,
            "Categoría": current_cats,
            "Chunks": doc.chunk_count,
            "Fecha": doc.upload_date.strftime("%Y-%m-%d %H:%M"),
            "Eliminar": False
        })
    
    df = pd.DataFrame(data)
    
    st.markdown("### 📋 Lista de Documentos")
    st.caption("Selecciona un documento para editar sus categorías.")
    
    if "Seleccionar" not in df.columns:
        df.insert(0, "Seleccionar", False)

    edited_df = st.data_editor(
        df,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn("Editar", default=False),
            "Eliminar": st.column_config.CheckboxColumn("Borrar?", default=False),
            "Categoría": st.column_config.ListColumn("Categorías (Actuales)", width="large")
        },
        disabled=["ID", "Archivo", "Categoría", "Chunks", "Fecha"],
        hide_index=True,
        use_container_width=True,
        key="inventory_table"
    )

    # --- EDIT LOGIC ---
    selected_rows = edited_df[edited_df["Seleccionar"] == True]
    
    if not selected_rows.empty:
        target_row = selected_rows.iloc[-1]
        fname = target_row["Archivo"]
        current_cats = target_row["Categoría"]
        
        st.divider()
        st.subheader(f"✏️ Editando: {fname}")
        
        with st.form("edit_category_form"):
            new_categories = st.multiselect(
                "Selecciona Categorías (Máximo 3)",
                options=valid_categories,
                default=[c for c in current_cats if c in valid_categories],
                max_selections=3,
                help="Elige las etiquetas que mejor describan este documento."
            )
            
            if st.form_submit_button("💾 Guardar Cambios"):
                if set(new_categories) != set(current_cats):
                    with st.spinner("Actualizando base de datos y vectores..."):
                        if kb_service.update_document_category(fname, new_categories):
                            st.success(f"✅ Documento '{fname}' actualizado correctamente.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error actualizando documento.")
                else:
                    st.info("No se detectaron cambios en las categorías.")
        
        # --- CHUNK INSPECTOR ---
        st.divider()
        with st.expander("🔎 Inspector de Contenido (Chunks)", expanded=True):
            st.caption(f"Visualizando vectores para: **{fname}**")
            
            with st.spinner("Recuperando vectores de Qdrant..."):
                chunks = kb_service.fetch_vectors(fname, limit=1000)
                
            if chunks:
                st.info(f"✅ Se encontraron {len(chunks)} fragmentos indexados.")
                
                chunk_data = []
                for c in chunks:
                    chunk_data.append({
                        "ID": str(c['id'])[:8] + "...",
                        "Inicio del Texto": c['content'][:80].replace("\n", " ") + "...",
                        "Longitud": len(c['content']),
                        "full_obj": c
                    })
                
                st.dataframe(
                    pd.DataFrame(chunk_data).drop(columns=["full_obj"]),
                    use_container_width=True,
                    hide_index=True
                )
                
                st.markdown("#### 👁️ Detalle del Fragmento")
                selected_chunk_idx = st.selectbox(
                    "Selecciona un ID para ver contenido completo",
                    options=range(len(chunks)),
                    format_func=lambda i: f"Chunk {i+1} ({str(chunks[i]['id'])[:6]})"
                )
                
                target_chunk = chunks[selected_chunk_idx]
                st.text_area(
                    "Contenido Completo",
                    value=target_chunk['content'],
                    height=200,
                    disabled=True
                )
                with st.expander("Ver Metadatos Completos"):
                    st.json(target_chunk['metadata'])
            else:
                st.warning("⚠️ No se encontraron chunks para este documento.")

    else:
        st.info("👆 Selecciona la casilla 'Editar' en la tabla superior para ver las opciones de modificación y el inspector de chunks.")

    # --- DELETE LOGIC ---
    to_delete = edited_df[edited_df["Eliminar"] == True]
    if not to_delete.empty:
        st.divider()
        st.error(f"⚠️ Seleccionaste {len(to_delete)} documentos para eliminar.")
        if st.button("CONFIRMAR ELIMINACIÓN", type="primary"):
            for index, row in to_delete.iterrows():
                fname = row["Archivo"]
                kb_service.delete_document(fname)
            st.success("Documentos eliminados.")
            st.rerun()

def render_rag_tester():
    st.title("🔍 Probador RAG")
    st.markdown("Simula búsquedas para verificar qué información recupera el agente.")
    
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            query = st.text_input("Escribe tu pregunta o consulta:", placeholder="Ej: ¿Cuánto cuesta el programa?")
        with c2:
            chunk_limit = st.number_input("Nº Chunks", min_value=1, max_value=20, value=5, help="Cantidad de fragmentos a recuperar")
        
        valid_categories = kb_service.get_valid_categories()
        filters = st.multiselect(
            "Filtrar por Categoría (Opcional)",
            valid_categories,
            default=[]
        )
        
        if st.button("🔎 Buscar en Base de Conocimiento", type="primary"):
            if query:
                filter_dict = {"doc_category": filters} if filters else {}
                with st.spinner("Buscando y rerankeando..."):
                    results = kb_service.search(query, limit=chunk_limit, filters=filter_dict, return_raw=True)
                
                if results:
                    st.success(f"✅ Se encontraron {len(results)} fragmentos relevantes.")
                    st.divider()
                    
                    cols = st.columns(2)
                    for i, item in enumerate(results):
                        with cols[i % 2]:
                            score = item.get('score', 0)
                            content = item.get('text', '')
                            meta = item.get('meta', {})
                            source = meta.get('source', 'Unknown')
                            category = meta.get('doc_category', 'General')
                            strategy = meta.get('strategy', 'Standard')
                            
                            # Normalize category if list
                            if isinstance(category, list):
                                category = ", ".join(category)
                                
                            # Score color logic
                            score_color = "green" if score > 0.7 else "orange" if score > 0.5 else "red"
                            
                            with st.container(border=True):
                                st.markdown(f"**#{i+1}** | :{score_color}[Score: {score:.4f}]")
                                st.caption(f"📂 `{source}`\n\n🏷️ `{category}`")
                                
                                with st.expander("📄 Contenido", expanded=True):
                                    st.markdown(content)
                                    if strategy == "small_to_big_contextual":
                                        st.info("🧠 Estrategia: Small-to-Big (Contextual)")
                                
                                with st.expander("ℹ️ Metadatos Completos"):
                                    st.json(meta)
                else:
                    st.warning("No se encontró información relevante.")

# --- UTILS FOR AUDIT (KEEPING THEM HERE AS THEY ARE UI HELPERS FOR DIFFING) ---
def get_state_diff(state_a, state_b):
    # ... (Keeping logic as it is purely presentation logic for diffs)
    if not state_a: state_a = {}
    if not state_b: state_b = {}
    diff = {}
    ignore_keys = ["messages", "user_id"]
    all_keys = set(state_a.keys()) | set(state_b.keys())
    for k in all_keys:
        if k in ignore_keys: continue
        val_a = state_a.get(k)
        val_b = state_b.get(k)
        if val_a == val_b: continue
        if isinstance(val_a, dict) and isinstance(val_b, dict):
            sub_diff = {}
            sub_keys = set(val_a.keys()) | set(val_b.keys())
            for sk in sub_keys:
                s_val_a = val_a.get(sk)
                s_val_b = val_b.get(sk)
                if s_val_a != s_val_b:
                    if s_val_a is None and s_val_b is None: continue
                    sub_diff[sk] = {"from": s_val_a, "to": s_val_b}
            if sub_diff: diff[k] = {"type": "dict_update", "changes": sub_diff}
        else:
            diff[k] = {"from": val_a, "to": val_b}
    return diff

def render_user_profile_card(user):
    with st.container(border=True):
        st.markdown(f"### 👤 {user.full_name or 'Usuario Sin Nombre'}")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("IDs")
            st.code(f"UUID: {user.id}\nTG: {user.telegram_id}\nWA: {user.whatsapp_id}", language="text")
        with c2:
            st.caption("Contacto")
            prof = user.profile_data or {}
            email_display = user.email or prof.get("email") or '-'
            phone_display = user.phone or prof.get("phone") or '-'
            st.text(f"Email: {email_display}")
            st.text(f"Phone: {phone_display}")
        with c3:
            st.caption("Data Base")
            st.text(f"Creado: {user.created_at.strftime('%Y-%m-%d')}")
        st.divider()
        st.markdown("**🧠 Perfil Psigráfico (Profile Data)**")
        if user.profile_data:
            st.json(user.profile_data, expanded=False)
        else:
            st.info("Sin datos de perfil.")

def _render_timeline_message(message):
    with st.chat_message(message.role):
        st.write(message.content)
        st.caption(f"{message.created_at.strftime('%H:%M:%S')}")

def _render_timeline_trace(trace):
    diff = get_state_diff(trace.input_state, trace.output_state)
    has_changes = len(diff) > 0
    icon = "⚡" if not has_changes else "🔄"
    profile_updates = {}
    if "user_profile" in diff and diff["user_profile"]["type"] == "dict_update":
        profile_updates = diff["user_profile"]["changes"]

    with st.expander(f"{icon} [{trace.created_at.strftime('%H:%M:%S')}] Nodo: {trace.node_name} ({trace.execution_time_ms:.0f}ms)"):
        col_main, col_insights = st.columns([3, 1])
        with col_insights:
            if profile_updates:
                st.success("🧠 **Aprendizaje Nuevo**")
                for k, v in profile_updates.items():
                    val_to = v['to']
                    if val_to:
                        st.markdown(f"**{k}:**")
                        st.code(str(val_to), language="text")
            else:
                st.caption("Sin datos nuevos del usuario")

        with col_main:
            if trace.llm_logs:
                st.info("🤖 **Actividad Cognitiva (LLM)**")
                for log in trace.llm_logs:
                    model_lower = log.model.lower() if log.model else "unknown"
                    if "gpt" in model_lower or "openai" in model_lower:
                        provider_icon = "🟢"
                        provider_name = "OpenAI"
                    elif "gemini" in model_lower:
                        provider_icon = "🔵"
                        provider_name = "Gemini"
                    else:
                        provider_icon = "⚪"
                        provider_name = "Other"

                    c_prov, c_model, c_tokens = st.columns([1.5, 2, 2.5])
                    with c_prov: st.markdown(f"**Proveedor:**\n\n{provider_icon} {provider_name}")
                    with c_model: st.markdown(f"**Modelo:**\n\n`{log.model}`")
                    with c_tokens: st.markdown(f"**Consumo (Tokens):**\n\n📥 `{log.tokens_input}` | 📤 `{log.tokens_output}`")

                    t1, t2 = st.tabs(["📤 Prompt (Entrada)", "📥 Respuesta (Salida)"])
                    with t1: st.text_area("Prompt Renderizado", log.prompt_rendered, height=200, key=f"p_{log.id}")
                    with t2: st.markdown(log.response_text) 
                    
                    if log.metadata_info and log.metadata_info.get("rag_context"):
                        with st.expander("📚 Contexto RAG Recuperado (Chunks)"):
                            st.markdown(log.metadata_info.get("rag_context"))
                    st.divider()

            st.markdown("#### 📺 Estado del Agente (AgentState)")
            tab_state_in, tab_state_out = st.tabs(["▶️ Inicial", "⏹️ Final (Output)"])
            with tab_state_in: st.json(trace.input_state)
            with tab_state_out:
                st.json(trace.output_state)
                if has_changes:
                    st.divider()
                    st.caption("✨ **Detalle de Cambios (Diff):**")
                    for key, change in diff.items():
                        if key == "user_profile": continue 
                        if change.get("type") == "dict_update":
                            st.markdown(f"**🔹 {key} (Actualizado):**")
                            for sub_k, sub_c in change["changes"].items():
                                val_from = sub_c['from']
                                val_to = sub_c['to']
                                st.markdown(f"- `{sub_k}`: <span style='color:red'>`{val_from}`</span> ➝ <span style='color:green'>`{val_to}`</span>", unsafe_allow_html=True)
                        else:
                            val_from = change['from']
                            val_to = change['to']
                            st.markdown(f"**🔹 {key}:** <span style='color:red'>`{val_from}`</span> ➝ <span style='color:green'>`{val_to}`</span>", unsafe_allow_html=True)

def render_audit_view():
    st.title("🕵️ Auditoría de Conversaciones")
    db = SessionLocal()
    repo = AuditRepository(db)
    try:
        recent_users = repo.get_recent_users(limit=20)
        if not recent_users:
            st.warning("No hay actividad reciente.")
            return
        user_options = {f"{u.full_name or 'Anon'} ({u.id}) - {t.strftime('%m/%d %H:%M')}": u for u, t in recent_users}
        selected_label = st.selectbox("Seleccionar Usuario", list(user_options.keys()))
        user = user_options[selected_label]
        user_id = user.id
        render_user_profile_card(user)
        if st.button("🗑️ Borrar Historial de este Usuario"):
            repo.clear_user_history(user_id) # Renamed from clear_user_conversation
            st.success("Historial borrado.")
            st.rerun()
        st.divider()
        st.subheader("📜 Línea de Tiempo")
        messages = db.query(Message).filter(Message.user_id == user_id).order_by(Message.created_at).all()
        traces = db.query(AgentTrace).filter(AgentTrace.user_id == user_id).order_by(AgentTrace.created_at).all()
        timeline = []
        for m in messages: timeline.append({"type": "msg", "obj": m, "time": m.created_at})
        for t in traces: timeline.append({"type": "trace", "obj": t, "time": t.created_at})
        timeline.sort(key=lambda x: x["time"])
        for item in timeline:
            if item["type"] == "msg": _render_timeline_message(item["obj"])
            else: _render_timeline_trace(item["obj"])
    finally:
        db.close()

def render_prompt_manager():
    st.title("📝 Gestión de Prompts")
    # ... (Keeping Prompt Manager as it uses DB directly for Prompts, which is fine for Admin)
    # Could be moved to a PromptService, but for now we focused on KnowledgeBase.
    # To keep "Clean Code", I'll just keep it here as it's Admin specific logic.
    # (Abbreviated for brevity, I should probably copy the whole thing or leave it if I want to save tokens, but I MUST replace the whole file. So I will paste the whole function.)
    
    with st.expander("🗺️ Mapa de Nodos y Prompts del Agente", expanded=True):
        st.markdown("Documentación viva de la arquitectura del agente.")
        nodes_data = [
            {"Nombre": "entry", "Objetivo": "Inicializar sesión y validar estado", "Resumen del Flujo": "Entry -> Router", "Herramientas": "N/A", "State Modificado": "current_state", "Prompt (Modelo)": "N/A", "Objetivo del Prompt": "N/A"},
            {"Nombre": "router", "Objetivo": "Clasificar intención y seguridad (Semantic + Regex)", "Resumen del Flujo": "Router -> Manager | Generator", "Herramientas": "FastEmbed (Semántico) + Regex (Guardrails)", "State Modificado": "router_outcome, objection_type, latest_reasoning", "Prompt (Modelo)": "N/A", "Objetivo del Prompt": "N/A"},
            {"Nombre": "manager", "Objetivo": "Cerebro Cognitivo: Decide estado y estrategia (CoT)", "Resumen del Flujo": "Manager -> Generator", "Herramientas": "LLM (Smart)", "State Modificado": "current_state, user_profile, disqualification_reason, latest_reasoning", "Prompt (Modelo)": "state_transition.j2, summary_generator.j2", "Objetivo del Prompt": "Razonamiento paso a paso (CoT) para transiciones de funnel"},
            {"Nombre": "generator", "Objetivo": "Generar respuesta persuasiva y empática", "Resumen del Flujo": "Generator -> Financial", "Herramientas": "LLM (Fast), RAG (HyDE + Hybrid), Scripts Registry", "State Modificado": "messages", "Prompt (Modelo)": "sales_system.j2, hyde_generator.j2, objection_handling.j2", "Objetivo del Prompt": "Generar respuesta final, alucinar documento ideal (HyDE), manejar objeciones críticas"},
            {"Nombre": "financial", "Objetivo": "Corrección determinista de datos duros (Precios/Fechas)", "Resumen del Flujo": "Financial -> END", "Herramientas": "String Replacement", "State Modificado": "messages (content overwrite)", "Prompt (Modelo)": "N/A", "Objetivo del Prompt": "N/A"}
        ]
        df_nodes = pd.DataFrame(nodes_data)
        st.table(df_nodes)

    st.markdown("Visualiza y edita los prompts del sistema en caliente.")
    db = SessionLocal()
    try:
        keys = db.query(PromptVersion.key).distinct().all()
        keys = [k[0] for k in keys]
        if not keys:
            st.info("No hay prompts registrados en la base de datos.")
            return
        selected_key = st.selectbox("Seleccionar Prompt", keys)
        current_version = db.execute(select(PromptVersion).where(PromptVersion.key == selected_key, PromptVersion.is_active == True).order_by(desc(PromptVersion.version))).scalars().first()
        if not current_version:
            st.error(f"No hay versión activa para '{selected_key}'")
            return
        with st.expander("ℹ️ Metadatos e Información", expanded=False):
            meta = current_version.metadata_info or {}
            c1, c2 = st.columns(2)
            c1.markdown(f"**Nodo Objetivo:** `{meta.get('target_node', 'N/A')}`")
            c1.markdown(f"**Modelo Sugerido:** `{meta.get('target_model', 'N/A')}`")
            c2.markdown(f"**Variables:** `{', '.join(meta.get('input_variables', []))}`")
            st.caption(f"Descripción: {meta.get('description', 'Sin descripción')}")
        st.subheader(f"Editor: {selected_key} (v{current_version.version})")
        new_content = st.text_area("Contenido (Jinja2)", value=current_version.content, height=400, help="Edita el template. Ten cuidado con las variables {{ var }}.")
        st.markdown("---")
        col_save, col_hist = st.columns([2, 1])
        with col_save:
            change_reason = st.text_input("Motivo del cambio (Obligatorio)", placeholder="Ej: Ajuste de tono para cierre más agresivo")
            if st.button("💾 Guardar Nueva Versión", type="primary", disabled=not change_reason):
                if new_content == current_version.content:
                    st.warning("No has realizado cambios en el texto.")
                else:
                    new_version_num = current_version.version + 1
                    current_version.is_active = False 
                    new_prompt = PromptVersion(key=selected_key, version=new_version_num, content=new_content, is_active=True, change_reason=change_reason, author_id="admin_ui", metadata_info=current_version.metadata_info)
                    db.add(new_prompt)
                    db.commit()
                    st.success(f"✅ Versión {new_version_num} creada. (El cambio se aplicará según la política de caché del servidor).")
                    st.rerun()
        with col_hist:
            st.markdown("### Historial")
            history = db.execute(select(PromptVersion).where(PromptVersion.key == selected_key).order_by(desc(PromptVersion.version)).limit(10)).scalars().all()
            for h in history:
                icon = "🟢" if h.is_active and h.id == current_version.id else "⚪"
                st.text(f"{icon} v{h.version} - {h.created_at.strftime('%m/%d %H:%M')}\n   Reason: {h.change_reason}")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        db.close()

def render_settings_view():
    st.title("⚙️ Configuración")
    with st.expander("⚠️ Zona de Peligro", expanded=True):
        st.error("Acciones destructivas y mantenimiento")
        col_maint, col_danger = st.columns(2)
        with col_maint:
            st.subheader("🛠️ Mantenimiento")
            if st.button("🔄 Sincronizar DB desde Vectores (Qdrant)"):
                with st.spinner("Escaneando Qdrant y reconstruyendo índice..."):
                    try:
                        stats = kb_service.sync_from_qdrant()
                        st.success(f"Sincronización completada: {stats}")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al sincronizar: {e}")
        with col_danger:
            st.subheader("🔥 Destructivo")
            if st.button("🔥🔥 Reiniciar TODA la Base de Conocimiento"):
                kb_service.reset_knowledge_base()
                st.success("Base de datos vectorial reiniciada.")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.header("🧠 Visionarias Brain")
    
    st.markdown("### 📊 Operaciones")
    op_selection = st.radio(
        "Operaciones",
        ["Dashboard", "Auditoría", "Configuración"],
        label_visibility="collapsed"
    )
    
    st.markdown("### 📚 Conocimiento")
    kb_selection = st.radio(
        "Conocimiento",
        ["Centro de Conocimiento", "Gestión de Prompts"],
        label_visibility="collapsed"
    )
    
    menu_selection = op_selection # Default fallback logic
    # Logic to prioritize the last clicked group is tricky in pure Streamlit radio.
    # We will use a simpler approach: A single radio with headers simulated or just grouped names.
    # But for better UX, let's merge them into a single list with visually distinct groups if possible, 
    # or just check which one changed. 
    # For simplicity and robustness in this "Hostinger-like" refactor:
    
    # Let's override the variable based on the section
    # Note: This is a limitation of Streamlit sidebar. 
    # Let's revert to a single radio but with emojis for grouping visual cues.
    pass 

# RE-IMPLEMENTING SIDEBAR WITH SINGLE RADIO FOR STABILITY
with st.sidebar:
    # Clear previous widgets
    pass

with st.sidebar:
    st.header("🧠 Visionarias Brain")
    
    menu_selection = st.radio(
        "Navegación",
        [
            "🏠 Dashboard",
            "📚 Conocimiento (Knowledge)",
            "📝 Gestión de Prompts",
            "🕵️ Auditoría",
            "⚙️ Configuración"
        ],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption(f"Env: {os.getenv('PROFILE', 'dev')}")

# --- ROUTER ---
main_container = st.empty()
with main_container.container():
    if "Dashboard" in menu_selection: render_dashboard()
    elif "Conocimiento" in menu_selection: render_knowledge_hub()
    elif "Prompts" in menu_selection: render_prompt_manager()
    elif "Auditoría" in menu_selection: render_audit_view()
    elif "Configuración" in menu_selection: render_settings_view()
