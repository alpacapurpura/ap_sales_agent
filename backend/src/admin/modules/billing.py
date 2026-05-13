"""Admin module — Planes & Billing.

Manage billing plans and tenant subscriptions without code changes.

Three views:
1. **Planes** — list 5 plan_config rows; inline edit numeric caps + toggle
   is_default atomically (UPDATE old=false + new=true in a single transaction).
2. **Suscripciones** — tenants with their plan_id + current-cycle spend from
   mv_daily_llm_cost_per_tenant_v2 (best-effort; shows N/A when MV unavailable).
3. **Overrides** — per-tenant custom_overrides JSONB: textarea + validate + save.

is_default toggle invariant (PM Q6):
  - Exactly one plan row has is_default=TRUE (partial unique index at DB level).
  - Toggle is atomic: BEGIN; UPDATE plan_config SET is_default=FALSE; UPDATE
    plan_config SET is_default=TRUE WHERE plan_id=new; COMMIT.

User-facing copy: español neutro LatAm (tuteo, sin voseo) per
``.claude/rules/spanish-text.md``.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
import streamlit as st
from luana_core_platform.core.database import SessionLocal

# Billing table names (string constants — no cross-module ORM import from shared.billing)
_PLAN_TABLE = "plan_config"
_SUB_TABLE = "tenant_subscription"
_MV_COST = "mv_daily_llm_cost_per_tenant_v2"


# ── DB helpers (sync — admin panel uses sync SessionLocal) ───────────────────


def _fetch_plans() -> list[dict[str, Any]]:
    """Return all plan_config rows ordered by llm_budget_total_usd."""
    from sqlalchemy import text

    db = SessionLocal()
    try:
        rows = (
            db.execute(
                text(
                    "SELECT plan_id, display_name, llm_budget_total_usd, "
                    "sales_agent_reserved_pct, max_outbound_msg_per_day, "
                    "max_campaigns_active, max_segment_size, max_contacts_total, "
                    "features, is_active, is_default "
                    "FROM plan_config ORDER BY llm_budget_total_usd ASC"
                )
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]
    finally:
        db.close()


def _fetch_tenant_subscriptions() -> list[dict[str, Any]]:
    """Return all active tenant_subscription rows joined with tenant name."""
    from sqlalchemy import text

    db = SessionLocal()
    try:
        rows = (
            db.execute(
                text(
                    "SELECT ts.tenant_id, ts.plan_id, ts.cycle_anchor_day, "
                    "ts.custom_overrides, ts.trial_ends_at, ts.activated_at, "
                    "t.name AS tenant_name "
                    "FROM tenant_subscription ts "
                    "LEFT JOIN tenants t ON t.id = ts.tenant_id "
                    "WHERE ts.deleted_at IS NULL "
                    "ORDER BY t.name ASC"
                )
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]
    finally:
        db.close()


def _fetch_cycle_spend() -> dict[str, Decimal]:
    """Return {tenant_id: total_cost_usd} from MV for the current 25-day cycle.

    Best-effort: returns empty dict if MV unavailable or errors.
    """
    from sqlalchemy import text

    db = SessionLocal()
    try:
        rows = (
            db.execute(
                text(
                    "SELECT tenant_id::text, SUM(total_cost_usd) AS spend "
                    f"FROM {_MV_COST} "
                    "WHERE metric_date >= date_trunc('month', CURRENT_DATE) "
                    "GROUP BY tenant_id"
                )
            )
            .mappings()
            .all()
        )
        return {str(r["tenant_id"]): Decimal(str(r["spend"] or 0)) for r in rows}
    except Exception:  # noqa: BLE001 — best-effort, admin panel never crashes
        return {}
    finally:
        db.close()


def _update_plan_atomic(plan_id: str, updates: dict[str, Any], set_default: bool) -> tuple[bool, str]:
    """Persist plan edits. If set_default=True, atomically clears prior default.

    Returns (success, message).
    """
    from sqlalchemy import text

    db = SessionLocal()
    try:
        set_clauses = ", ".join(f"{k} = :{k}" for k in updates)
        updates["plan_id"] = plan_id
        if set_default:
            # PM Q6: atomic is_default toggle — must run in one transaction.
            db.execute(text(f"UPDATE {_PLAN_TABLE} SET is_default = FALSE"))
            db.execute(
                text(f"UPDATE {_PLAN_TABLE} SET {set_clauses}, is_default = TRUE WHERE plan_id = :plan_id"),
                updates,
            )
        else:
            db.execute(
                text(f"UPDATE {_PLAN_TABLE} SET {set_clauses}, is_default = FALSE WHERE plan_id = :plan_id"),
                updates,
            )
        db.commit()
        return True, "Plan actualizado."
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return False, f"Error al actualizar el plan: {exc}"
    finally:
        db.close()


def _update_tenant_overrides(tenant_id: str, overrides: dict[str, Any]) -> tuple[bool, str]:
    """Persist custom_overrides JSONB for a tenant subscription.

    Returns (success, message).
    """
    from sqlalchemy import text

    db = SessionLocal()
    try:
        db.execute(
            text(
                f"UPDATE {_SUB_TABLE} SET custom_overrides = :overrides "
                "WHERE tenant_id = :tenant_id AND deleted_at IS NULL"
            ),
            {"overrides": json.dumps(overrides), "tenant_id": tenant_id},
        )
        db.commit()
        return True, "Overrides actualizados."
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        return False, f"Error al actualizar overrides: {exc}"
    finally:
        db.close()


# ── Render helpers ───────────────────────────────────────────────────────────


def _format_usd(val: Decimal | float | str | None) -> str:
    if val is None:
        return "—"
    try:
        return f"${Decimal(str(val)):,.2f}"
    except (InvalidOperation, TypeError):
        return str(val)


def _render_planes_tab() -> None:
    """Inline edit for plan_config rows."""
    st.subheader("Planes disponibles")
    st.caption(
        "Edita los caps de presupuesto y mensajes sin migraciones. "
        "El toggle 'Por defecto' es atómico: desmarca el plan anterior automáticamente."
    )

    plans = _fetch_plans()
    if not plans:
        st.warning("No se encontraron planes. Verifica que la migración 110 se haya ejecutado.")
        return

    for plan in plans:
        pid = plan["plan_id"]
        with st.expander(f"{'🌟 ' if plan['is_default'] else ''}{plan['display_name']} (`{pid}`)", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                new_budget = st.number_input(
                    "Presupuesto LLM (USD)",
                    value=float(plan["llm_budget_total_usd"]),
                    min_value=0.01,
                    step=1.0,
                    key=f"budget_{pid}",
                )
                new_sa_pct = st.number_input(
                    "% reservado para Sales Agent (0–1)",
                    value=float(plan["sales_agent_reserved_pct"]),
                    min_value=0.0,
                    max_value=1.0,
                    step=0.05,
                    key=f"sa_pct_{pid}",
                )

            with col2:
                new_outbound = st.number_input(
                    "Máx. mensajes outbound/día",
                    value=int(plan["max_outbound_msg_per_day"] or 0),
                    min_value=0,
                    step=100,
                    key=f"outbound_{pid}",
                    help="0 = sin límite",
                )
                new_campaigns = st.number_input(
                    "Máx. campañas activas",
                    value=int(plan["max_campaigns_active"] or 0),
                    min_value=0,
                    step=1,
                    key=f"campaigns_{pid}",
                    help="0 = sin límite",
                )

            with col3:
                new_contacts = st.number_input(
                    "Máx. contactos totales",
                    value=int(plan["max_contacts_total"] or 0),
                    min_value=0,
                    step=1000,
                    key=f"contacts_{pid}",
                    help="0 = sin límite",
                )
                is_active = st.checkbox("Plan activo", value=plan["is_active"], key=f"active_{pid}")
                set_default = st.checkbox(
                    "Marcar como plan por defecto",
                    value=plan["is_default"],
                    key=f"default_{pid}",
                    help="Solo un plan puede ser el default (invariant PM Q6).",
                )

            # Computed preview
            budget_dec = Decimal(str(new_budget))
            sa_pct_dec = Decimal(str(new_sa_pct))
            sa_pool = (budget_dec * sa_pct_dec).quantize(Decimal("0.01"))
            others_pool = (budget_dec - sa_pool).quantize(Decimal("0.01"))
            st.info(
                f"Pool Sales Agent: **{_format_usd(sa_pool)}** | Pool Copilot/Otros: **{_format_usd(others_pool)}**"
            )

            if st.button("Guardar cambios", key=f"save_{pid}"):
                updates = {
                    "display_name": plan["display_name"],
                    "llm_budget_total_usd": new_budget,
                    "sales_agent_reserved_pct": new_sa_pct,
                    "max_outbound_msg_per_day": new_outbound if new_outbound > 0 else None,
                    "max_campaigns_active": new_campaigns if new_campaigns > 0 else None,
                    "max_contacts_total": new_contacts if new_contacts > 0 else None,
                    "is_active": is_active,
                }
                ok, msg = _update_plan_atomic(pid, updates, set_default=set_default)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


def _render_suscripciones_tab() -> None:
    """Tenant subscription list with current-cycle spend."""
    st.subheader("Suscripciones por tenant")
    st.caption(
        "Gasto del ciclo actual tomado de `mv_daily_llm_cost_per_tenant_v2`. "
        "Si la MV no se refresca hace más de 1h, el gasto puede estar desactualizado."
    )

    subs = _fetch_tenant_subscriptions()
    spend_by_tenant = _fetch_cycle_spend()

    if not subs:
        st.info("No hay suscripciones activas. Los tenants sin suscripción usan el plan por defecto.")
        return

    data = []
    for s in subs:
        tid = str(s["tenant_id"])
        spend = spend_by_tenant.get(tid)
        data.append(
            {
                "Tenant": s.get("tenant_name") or tid[:8],
                "Plan": s["plan_id"],
                "Ancla ciclo": s.get("cycle_anchor_day", 25),
                "Trial hasta": str(s["trial_ends_at"])[:10] if s.get("trial_ends_at") else "—",
                "Gasto ciclo (USD)": _format_usd(spend) if spend is not None else "N/A",
                "Overrides": "Sí" if s.get("custom_overrides") else "No",
                "Tenant ID": tid,
            }
        )

    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_overrides_tab() -> None:
    """Per-tenant custom_overrides JSONB editor."""
    st.subheader("Overrides por tenant")
    st.caption(
        "Los overrides sobreescriben los valores del plan base solo para ese tenant. "
        "Formato JSON. Campos válidos: cualquier campo de `PlanConfig` (ej. `llm_budget_total_usd`, "
        "`max_outbound_msg_per_day`)."
    )

    subs = _fetch_tenant_subscriptions()
    if not subs:
        st.info("No hay suscripciones activas.")
        return

    tenant_options = {
        f"{s.get('tenant_name') or str(s['tenant_id'])[:8]} ({str(s['tenant_id'])[:8]}...)": str(s["tenant_id"])
        for s in subs
    }

    selected_label = st.selectbox("Selecciona tenant", list(tenant_options.keys()), key="override_tenant_select")
    selected_tid = tenant_options[selected_label]
    selected_sub = next((s for s in subs if str(s["tenant_id"]) == selected_tid), None)

    if selected_sub is None:
        st.warning("No se encontró la suscripción.")
        return

    current_overrides = selected_sub.get("custom_overrides") or {}
    current_json = json.dumps(current_overrides, indent=2, default=str)

    new_json = st.text_area(
        "custom_overrides (JSON)",
        value=current_json,
        height=200,
        key=f"overrides_editor_{selected_tid}",
        help="Edita los overrides del tenant. Deja `{}` para sin overrides.",
    )

    # Validate JSON before save
    parsed: dict[str, Any] | None = None
    try:
        parsed = json.loads(new_json)
        if not isinstance(parsed, dict):
            st.error("El JSON debe ser un objeto (diccionario).")
            parsed = None
        else:
            st.success("JSON válido.")
    except json.JSONDecodeError as exc:
        st.error(f"JSON inválido: {exc}")

    if parsed is not None and st.button("Guardar overrides", key=f"save_override_{selected_tid}"):
        ok, msg = _update_tenant_overrides(selected_tid, parsed)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)


# ── Public render function ───────────────────────────────────────────────────


def render_billing_admin() -> None:
    """Render the planes & billing admin page."""
    st.title("💳 Planes y Facturación")
    st.caption(
        "Gestión de planes de precios y suscripciones de tenants. "
        "Los cambios se aplican en tiempo real — sin migraciones ni reinicio."
    )

    tab_planes, tab_subs, tab_overrides = st.tabs(["📋 Planes", "👥 Suscripciones", "🔧 Overrides por Tenant"])

    with tab_planes:
        try:
            _render_planes_tab()
        except Exception as exc:  # noqa: BLE001 — admin panel never hard-crashes
            st.error(f"Error al cargar los planes: {exc}")

    with tab_subs:
        try:
            _render_suscripciones_tab()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error al cargar las suscripciones: {exc}")

    with tab_overrides:
        try:
            _render_overrides_tab()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Error al cargar los overrides: {exc}")
