"""Streamlit admin panel entry point.

Uses Streamlit's native multi-page routing via `st.navigation` so each option
gets an explicit URL path (e.g. `/comando`, `/salud`). Browser refresh and
deep links preserve the current page. To add a new option:

1. Add the module under `src/admin/modules/` exposing a `render_*()` function.
2. Create a matching file under `src/admin/pages/` that imports and calls it.
3. Append a `PageSpec` to `PAGE_SPECS` below.

Contract tests in `backend/tests/admin/test_admin_contract.py` enforce that
every file in `pages/` is registered here and wired to a render function.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

# Add project root to path to import src modules (keeps CLI invocation simple).
sys.path.append(str((Path(__file__).parent / "../..").resolve()))

# Bootstrap all SQLAlchemy mappers once so cross-module relationships resolve.
import src.shared.infrastructure.model_registry  # noqa: F401

# --- PAGE CONFIG (must run before any other st.* call) ---
st.set_page_config(
    page_title=os.getenv("ADMIN_TITLE", "SaaS Admin Panel"),
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS STYLES ---
st.markdown(
    """
<style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


@dataclass(frozen=True)
class PageSpec:
    """Single entry in the admin navigation.

    `slug` is both the URL path (`/<slug>`) and the filename
    stem under `src/admin/pages/`. Keeping them identical lets the contract
    test pair each file with its registration by filename alone.
    """

    slug: str
    title: str
    icon: str


# Order here drives sidebar order. Default page = first entry.
PAGE_SPECS: tuple[PageSpec, ...] = (
    PageSpec(slug="comando", title="Comando Central", icon="🎯"),
    PageSpec(slug="salud", title="Salud de Tenants", icon="🏥"),
    PageSpec(slug="inteligencia", title="Inteligencia Copilot", icon="🧠"),
    PageSpec(slug="conversaciones", title="Conversaciones", icon="💬"),
    PageSpec(slug="trazas", title="Trazas Copilot", icon="🔬"),
    PageSpec(slug="auditoria", title="Auditoría Sales Agent", icon="🔍"),
    PageSpec(slug="knowledge", title="Knowledge Base", icon="📚"),
    PageSpec(slug="capacidades", title="Capacidades Copilot", icon="🔧"),
    PageSpec(slug="proveedores", title="Proveedores Copilot", icon="🔌"),
    PageSpec(slug="brand-summaries", title="Brand Summary Lighthouse", icon="🪧"),
    PageSpec(slug="calendario", title="Calendario Comercial", icon="📅"),
    PageSpec(slug="tenants", title="Tenants (Clientes)", icon="🏢"),
    PageSpec(slug="usuarios", title="Usuarios", icon="👥"),
)

_PAGES_DIR = Path(__file__).parent / "pages"


def _build_pages() -> list[st.Page]:
    """Materialize `st.Page` objects from `PAGE_SPECS`."""
    pages: list[st.Page] = []
    for idx, spec in enumerate(PAGE_SPECS):
        page_file = _PAGES_DIR / f"{spec.slug}.py"
        pages.append(
            st.Page(
                str(page_file),
                title=f"{spec.icon} {spec.title}",
                url_path=spec.slug,
                default=(idx == 0),
            ),
        )
    return pages


def main() -> None:
    """Render the admin panel shell and delegate to the active page."""
    st.sidebar.title("🛠️ Panel Admin")
    st.sidebar.caption(f"Env: {os.getenv('PROFILE', 'dev')}")
    st.sidebar.divider()

    pages = _build_pages()
    active = st.navigation(pages, position="sidebar", expanded=True)
    active.run()


if __name__ == "__main__":
    main()
else:
    # Streamlit executes scripts top-to-bottom on every rerun, so call main()
    # when imported as a Streamlit entrypoint too.
    main()
