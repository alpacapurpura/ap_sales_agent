"""Admin page — LiteLLM Proxy virtual keys (read-only S3).

Thin wrapper per admin-panel.md contract:
- 1 PageSpec in app.py registry
- 1 pages/<slug>.py wrapper
- 1 modules/<slug>.py with render_* logic
"""

from src.admin.modules.llm_virtual_keys import render_llm_virtual_keys

render_llm_virtual_keys()
