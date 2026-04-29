---
globs: "backend/src/admin/**/*.py"
description: Stub — invoca backend-expert skill
---

# Admin Panel (Streamlit)

Registry-based `st.navigation`. Cada sidebar option = 1 `PageSpec` + 1 `pages/{slug}.py` wrapper + 1 `modules/{name}.py::render_*()`. Lógica solo en `modules/`.

Detalle (estructura, agregar opción, contract tests, smoke tests, Docker limits) en `backend-expert` skill → `references/admin-panel.md`.

**Prohibido:** lógica en `pages/*.py`, `st.set_page_config` fuera `app.py`, import cruzado `modules/A → modules/B` (excepto `_shared`), slug duplicado.
