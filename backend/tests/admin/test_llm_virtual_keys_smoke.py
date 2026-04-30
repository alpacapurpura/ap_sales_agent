"""Smoke test admin Streamlit page llm-virtual-keys (S3 PR-2 PI-2).

Read-only page lists virtual keys via LiteLLM Proxy ``/key/info`` endpoint.
CRUD UI deferred to S4 PR-1.

D-16: Streamlit registry pattern compliance + module render function.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_llm_virtual_keys_module_imports_cleanly() -> None:
    """Module loads without side effects."""
    import src.admin.modules.llm_virtual_keys as mod

    assert hasattr(mod, "render_llm_virtual_keys")
    assert callable(mod.render_llm_virtual_keys)


def test_llm_virtual_keys_page_wrapper_thin() -> None:
    """Page wrapper at admin/pages/llm-virtual-keys.py only delegates."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent
    page_path = repo_root / "src" / "admin" / "pages" / "llm-virtual-keys.py"
    content = page_path.read_text(encoding="utf-8")
    assert "render_llm_virtual_keys" in content
    # Wrapper must not contain business logic — just import + invoke.
    assert content.count("def ") <= 1, "Page wrapper should be thin (no extra functions)"


def test_llm_virtual_keys_registered_in_admin_app() -> None:
    """PageSpec llm-virtual-keys registered in PAGE_SPECS tuple."""
    from src.admin.app import PAGE_SPECS

    slugs = {spec.slug for spec in PAGE_SPECS}
    assert "llm-virtual-keys" in slugs


def test_llm_virtual_keys_fetch_returns_empty_on_error() -> None:
    """Fetch helper returns [] when proxy unreachable (graceful degradation)."""
    from src.admin.modules.llm_virtual_keys import _fetch_virtual_keys

    with patch("httpx.get", side_effect=Exception("connection refused")):
        result = _fetch_virtual_keys()
        assert result == []


def test_llm_virtual_keys_fetch_extracts_keys_field() -> None:
    """Fetch helper extracts list from LiteLLM /key/list response shape."""
    from src.admin.modules.llm_virtual_keys import _fetch_virtual_keys

    sample_response = MagicMock()
    sample_response.status_code = 200
    sample_response.json.return_value = {
        "keys": [
            {"key_alias": "tenant-a", "spend": 1.23, "models": ["openai/gpt-4o-mini"]},
        ]
    }
    sample_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=sample_response):
        result = _fetch_virtual_keys()
        assert len(result) == 1
        assert result[0]["key_alias"] == "tenant-a"


def test_fmt_budget_handles_none() -> None:
    """_fmt_budget(None) returns 'Sin límite'."""
    from src.admin.modules.llm_virtual_keys import _fmt_budget

    assert _fmt_budget(None) == "Sin límite"
    assert _fmt_budget(10.5) == "USD 10.5000"


def test_fmt_date_handles_none() -> None:
    """_fmt_date(None) returns em-dash."""
    from src.admin.modules.llm_virtual_keys import _fmt_date

    assert _fmt_date(None) == "—"
