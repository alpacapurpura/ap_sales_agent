"""Streamlit admin module para Calendario Comercial."""

import pandas as pd
import streamlit as st

from src.core.database import SessionLocal
from src.modules.commercial_calendar.application.calendar_event_service import (
    CalendarEventService,
)
from src.modules.commercial_calendar.domain.enums import EventCategory
from src.shared.domain.datetime_utils import utc_today

COUNTRIES = {
    "PE": "Perú",
    "CO": "Colombia",
    "MX": "México",
    "AR": "Argentina",
    "CL": "Chile",
    "EC": "Ecuador",
    "US": "Estados Unidos",
    "ES": "España",
    "BR": "Brasil",
}

CATEGORY_LABELS = {
    EventCategory.FERIADO.value: "🏖️ Feriado",
    EventCategory.CAMPANA.value: "📣 Campaña",
    EventCategory.CYBER.value: "💻 Cyber",
    EventCategory.SALE.value: "🏷️ Sale",
    EventCategory.DIA_ESPECIAL.value: "⭐ Día Especial",
    EventCategory.TEMPORADA.value: "📅 Temporada",
    EventCategory.CULTURAL.value: "🎭 Cultural",
    EventCategory.ELECCIONES.value: "🗳️ Elecciones",
    EventCategory.CUSTOM.value: "✏️ Custom",
}


def _get_service() -> tuple[CalendarEventService, object]:
    db = SessionLocal()
    return CalendarEventService(db), db


def render_commercial_calendar_page():
    st.title("📅 Calendario Comercial")

    # ── Controles globales ──────────────────────────────────────────────────
    col_pais, col_ano, col_info = st.columns([2, 1, 3])
    with col_pais:
        country_code = st.selectbox(
            "País",
            options=list(COUNTRIES.keys()),
            format_func=lambda k: f"{k} — {COUNTRIES[k]}",
            index=0,
        )
    with col_ano:
        year = st.number_input(
            "Año",
            min_value=2024,
            max_value=2030,
            value=utc_today().year,
            step=1,
        )

    service, db = _get_service()
    try:
        current_week, _current_year = service.get_current_week_number()
    finally:
        db.close()

    with col_info:
        st.metric("Semana actual", f"Semana {current_week} de {utc_today().year}")

    st.divider()

    tab_cal, tab_crear, tab_editar, tab_eliminar, tab_stats = st.tabs(
        [
            "📋 Calendario",
            "➕ Crear Evento",
            "✏️ Editar",
            "🗑️ Eliminar",
            "📊 Stats",
        ],
    )

    # ── TAB 1: CALENDARIO ───────────────────────────────────────────────────
    with tab_cal:
        service, db = _get_service()
        try:
            events = service.list_events(
                country_code=country_code,
                year=int(year),
                tenant_id=None,  # admin ve todo
            )
        finally:
            db.close()

        if not events:
            st.info(
                f"No hay eventos para {COUNTRIES.get(country_code, country_code)} {int(year)}.",
            )
        else:
            rows = [
                {
                    "Fecha": e.date.strftime("%d/%m/%Y"),
                    "Sem.": e.week_number,
                    "Nombre": e.name,
                    "Categoría": CATEGORY_LABELS.get(
                        e.category or "",
                        e.category or "—",
                    ),
                    "Fuente": "🔵 Sistema" if e.is_system else "🟢 Tenant",
                    "_week": e.week_number,
                    "_id": str(e.id),
                }
                for e in events
            ]

            df = pd.DataFrame(rows)

            # Highlight semana actual (year coincidente)
            if int(year) == utc_today().year:
                st.caption(f"✨ Semana actual resaltada: **Semana {current_week}**")

                def highlight_week(row):
                    if row["_week"] == current_week:
                        return ["background-color: #fef9c3"] * len(row)
                    return [""] * len(row)

                st.dataframe(
                    df[
                        [
                            "Fecha",
                            "Sem.",
                            "Nombre",
                            "Categoría",
                            "Fuente",
                            "_week",
                            "_id",
                        ]
                    ]
                    .style.apply(highlight_week, axis=1)
                    .hide(subset=["_week", "_id"], axis="columns"),
                    use_container_width=True,
                    height=500,
                )
            else:
                st.dataframe(
                    df[["Fecha", "Sem.", "Nombre", "Categoría", "Fuente"]],
                    use_container_width=True,
                    height=500,
                )

            st.caption(
                f"Total: **{len(events)} filas** ({len({e.name for e in events})} eventos únicos)",
            )

    # ── TAB 2: CREAR EVENTO ─────────────────────────────────────────────────
    with tab_crear:
        st.subheader("Crear Evento del Sistema")
        with st.form("form_crear"):
            c1, c2 = st.columns(2)
            with c1:
                pais = st.selectbox(
                    "País",
                    list(COUNTRIES.keys()),
                    format_func=lambda k: f"{k} — {COUNTRIES[k]}",
                )
                nombre = st.text_input("Nombre del evento")
                categoria = st.selectbox(
                    "Categoría",
                    [e.value for e in EventCategory],
                    format_func=lambda v: CATEGORY_LABELS.get(v, v),
                )
            with c2:
                fecha_inicio = st.date_input("Fecha inicio", value=utc_today())
                fecha_fin = st.date_input(
                    "Fecha fin (opcional — para rangos)",
                    value=None,
                )
            descripcion = st.text_area("Descripción (opcional)")
            submitted = st.form_submit_button("✅ Crear Evento(s)", type="primary")

        if submitted:
            if not nombre:
                st.error("El nombre es obligatorio.")
            else:
                service, db = _get_service()
                try:
                    created = service.create_event(
                        country_code=pais,
                        name=nombre,
                        date_start=fecha_inicio,
                        date_end=fecha_fin if fecha_fin and fecha_fin >= fecha_inicio else None,
                        category=categoria,
                        description=descripcion or None,
                        tenant_id=None,  # admin crea eventos del sistema
                    )
                    st.success(f"✅ {len(created)} fila(s) creada(s) para '{nombre}'.")
                finally:
                    db.close()

    # ── TAB 3: EDITAR ───────────────────────────────────────────────────────
    with tab_editar:
        st.subheader("Editar Evento")
        buscar = st.text_input("Buscar por nombre (parcial):", key="buscar_editar")
        if buscar:
            service, db = _get_service()
            try:
                all_events = service.list_events(
                    country_code=country_code,
                    year=int(year),
                    tenant_id=None,
                )
            finally:
                db.close()

            matches = [e for e in all_events if buscar.lower() in e.name.lower()]
            unique_names = list(dict.fromkeys(e.name for e in matches))

            if not unique_names:
                st.warning("No se encontraron eventos.")
            else:
                sel_name = st.selectbox("Seleccionar evento:", unique_names)
                sel_events = [e for e in matches if e.name == sel_name]
                sel_event = sel_events[0] if sel_events else None

                if sel_event:
                    with st.form("form_editar"):
                        nuevo_nombre = st.text_input("Nombre", value=sel_event.name)
                        nueva_cat = st.selectbox(
                            "Categoría",
                            [e.value for e in EventCategory],
                            index=[e.value for e in EventCategory].index(
                                sel_event.category,
                            )
                            if sel_event.category in [e.value for e in EventCategory]
                            else 0,
                            format_func=lambda v: CATEGORY_LABELS.get(v, v),
                        )
                        nueva_desc = st.text_area(
                            "Descripción",
                            value=sel_event.description or "",
                        )
                        st.caption(
                            f"⚠️ Solo se editará la primera fila encontrada ({sel_event.date})."
                            " Para rangos, eliminar y recrear.",
                        )
                        submitted_edit = st.form_submit_button(
                            "💾 Guardar cambios",
                            type="primary",
                        )

                    if submitted_edit:
                        service, db = _get_service()
                        try:
                            updated = service.update_event(
                                event_id=sel_event.id,
                                name=nuevo_nombre,
                                category=nueva_cat,
                                description=nueva_desc or None,
                            )
                            if updated:
                                st.success(f"✅ Evento '{updated.name}' actualizado.")
                            else:
                                st.error("No se pudo actualizar.")
                        finally:
                            db.close()

    # ── TAB 4: ELIMINAR ─────────────────────────────────────────────────────
    with tab_eliminar:
        st.subheader("Eliminar Evento")
        buscar_del = st.text_input(
            "Buscar por nombre (parcial):",
            key="buscar_eliminar",
        )
        if buscar_del:
            service, db = _get_service()
            try:
                all_events = service.list_events(
                    country_code=country_code,
                    year=int(year),
                    tenant_id=None,
                )
            finally:
                db.close()

            matches = [e for e in all_events if buscar_del.lower() in e.name.lower()]
            unique_names = list(dict.fromkeys(e.name for e in matches))

            if not unique_names:
                st.warning("No se encontraron eventos.")
            else:
                sel_name_del = st.selectbox(
                    "Seleccionar evento a eliminar:",
                    unique_names,
                )
                sel_events_del = [e for e in matches if e.name == sel_name_del]

                st.warning(
                    f"Se eliminarán **{len(sel_events_del)} filas** para '{sel_name_del}'.",
                )
                confirmar = st.checkbox("Confirmo que quiero eliminar estos eventos")
                if confirmar and st.button("🗑️ Eliminar", type="primary"):
                    service, db = _get_service()
                    try:
                        eliminados = 0
                        for e in sel_events_del:
                            if service.delete_event(e.id):
                                eliminados += 1
                        st.success(f"✅ {eliminados} fila(s) eliminada(s).")
                    finally:
                        db.close()

    # ── TAB 5: STATS ────────────────────────────────────────────────────────
    with tab_stats:
        service, db = _get_service()
        try:
            events = service.list_events(
                country_code=country_code,
                year=int(year),
                tenant_id=None,
            )
        finally:
            db.close()

        if not events:
            st.info("Sin datos para mostrar.")
        else:
            rows = [
                {
                    "month": e.date.month,
                    "week": e.week_number,
                    "category": e.category or "sin_categoria",
                }
                for e in events
            ]
            df = pd.DataFrame(rows)

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Eventos por mes")
                mes_counts = df.groupby("month").size().reset_index(name="count")
                mes_counts["mes"] = mes_counts["month"].apply(
                    lambda m: [
                        "Ene",
                        "Feb",
                        "Mar",
                        "Abr",
                        "May",
                        "Jun",
                        "Jul",
                        "Ago",
                        "Sep",
                        "Oct",
                        "Nov",
                        "Dic",
                    ][m - 1],
                )
                st.bar_chart(mes_counts.set_index("mes")["count"])

            with col_b:
                st.subheader("Eventos por categoría")
                cat_counts = (
                    df.groupby("category").size().reset_index(name="count").sort_values("count", ascending=False)
                )
                cat_counts["cat_label"] = cat_counts["category"].apply(
                    lambda v: CATEGORY_LABELS.get(v, v),
                )
                st.bar_chart(cat_counts.set_index("cat_label")["count"])

            st.subheader("Distribución semanal")
            week_counts = df.groupby("week").size().reset_index(name="count")
            st.bar_chart(week_counts.set_index("week")["count"])
