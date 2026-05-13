"""Admin module: Copilot provider registry inspector.

Surfaces the ``CopilotProvider`` plugins discovered at runtime — module id,
label, route prefixes, declared sub-port capabilities, tool group counts and
health status. Use this page to diagnose "why does the copilot not see X?"
without trawling structlog.

[COPILOT-PROVIDER-PATTERN]: see ``docs/domains/copilot/redesign-2026-04/``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import streamlit as st
from luana_core_copilot.application.discovery import (
    discover_providers,
    health,
    reset_discovery,
)
from luana_core_copilot.domain.module_registry import reset_module_registry_cache

if TYPE_CHECKING:
    from luana_core_copilot.domain.ports import CopilotProvider


def _capability_badge(label: str, *, present: bool) -> str:
    icon = "✅" if present else "—"
    return f"{icon} {label}"


def _provider_card(provider: CopilotProvider, *, healthy: bool, error: str | None) -> None:
    status = "🟢 OK" if healthy else f"🔴 {error or 'unknown'}"
    with st.container(border=True):
        st.markdown(f"### `{provider.module_id}` · {provider.label}")
        st.caption(status)

        data = provider.module_data()
        if data is not None:
            st.write(f"**Route prefix:** `{data.route_prefix}`")
            if data.keywords:
                st.write(f"**Keywords:** {', '.join(data.keywords)}")
            st.caption(data.description)
        else:
            st.caption("No introspectable module_data — provider exposes tools/workflows only.")

        cols = st.columns(4)
        cols[0].write(_capability_badge("tools", present=provider.tool_provider() is not None))
        cols[1].write(_capability_badge("workflows", present=provider.workflow_provider() is not None))
        cols[2].write(_capability_badge("summary", present=provider.summary_provider() is not None))
        cols[3].write(_capability_badge("context_inject", present=provider.context_injector() is not None))

        tool_provider = provider.tool_provider()
        if tool_provider is not None:
            groups = tool_provider.tool_groups()
            if groups:
                st.write("**Tool groups:**")
                for group_name, group_tools in groups.items():
                    tool_names = ", ".join(getattr(t, "name", repr(t)) for t in group_tools) or "—"
                    st.markdown(f"- `{group_name}` ({len(list(group_tools))}): {tool_names}")

        routes = provider.routes()
        if routes:
            st.write("**Provider routes:**")
            for route in routes:
                st.markdown(f"- `{route.prefix}` → groups: {', '.join(route.groups) or '(none)'}")


def render_copilot_providers() -> None:
    """Render the copilot provider registry inspector page."""
    st.title("🔌 Proveedores del Copilot")
    st.caption(
        "Plugins descubiertos en arranque. Cada módulo expone su CopilotProvider en"
        " `src/modules/{name}/copilot_provider/`."
    )

    reload_col, _ = st.columns([1, 6])
    if reload_col.button("🔄 Recargar", help="Vacía el caché de discovery y vuelve a escanear."):
        reset_discovery()
        reset_module_registry_cache()
        st.rerun()

    providers = discover_providers()
    health_snapshot = health()

    if not providers:
        st.error(
            "Discovery no encontró ningún provider. Verificá que cada módulo tenga"
            " `src/modules/{name}/copilot_provider/__init__.py` exportando"
            " `provider`. Logs: `copilot.discovery.empty`."
        )
        return

    st.metric("Providers cargados", len(providers))
    cols = st.columns(3)
    cols[0].metric("Saludables", sum(1 for h in health_snapshot.values() if h.healthy))
    cols[1].metric("Con error", sum(1 for h in health_snapshot.values() if not h.healthy))
    cols[2].metric(
        "Total tools",
        sum(
            sum(len(list(g)) for g in (p.tool_provider().tool_groups() if p.tool_provider() else {}).values())
            for p in providers.values()
        ),
    )

    for module_id in sorted(providers):
        provider = providers[module_id]
        h = health_snapshot.get(module_id)
        _provider_card(
            provider,
            healthy=h.healthy if h is not None else False,
            error=h.last_error if h is not None else None,
        )


__all__ = ("render_copilot_providers",)


# Backwards-compat alias for direct script invocation; the wrapper page uses
# the explicit name above.
_ = Any  # silence unused TYPE_CHECKING placeholder if added later
