"""Architectural fitness — campaigns API response_model enforcement.

Verifica que todos los endpoints de campaigns, segments y templates
declaran response_model= (PII allowlist pattern).

# [CAMPAIGNS-API-RESPONSE-MODEL-PR4-S1]
"""

from __future__ import annotations

import ast
import pathlib

_ROUTERS_DIR = pathlib.Path("src/modules/campaigns/api/routers")


def _collect_route_decorators(source: str) -> list[tuple[str, dict[str, str]]]:
    """Return list of (method, kwargs_str_map) for router.{get,post,patch,delete} calls."""
    tree = ast.parse(source)
    results: list[tuple[str, dict[str, str]]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call):
                continue
            func = deco.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in ("get", "post", "patch", "delete", "put"):
                continue
            kwargs = {kw.arg: ast.unparse(kw.value) for kw in deco.keywords if kw.arg}
            results.append((func.attr.upper(), kwargs))

    return results


class TestCampaignsAPIResponseModel:
    """Todos los endpoints de campaigns/segments/templates deben declarar response_model=."""

    def _check_router_file(self, router_path: pathlib.Path) -> None:
        source = router_path.read_text()
        routes = _collect_route_decorators(source)

        # DELETE endpoints (204 No Content) don't need response_model — they return None.
        non_delete_routes = [(method, kwargs) for method, kwargs in routes if method != "DELETE"]

        missing = []
        for method, kwargs in non_delete_routes:
            if "response_model" not in kwargs and "status_code" not in kwargs:
                # status_code=204 implies None response; skip. Else require response_model.
                missing.append(f"{method} {router_path.name}")
            elif (
                "response_model" not in kwargs
                and "status_code" in kwargs
                and "204" not in kwargs.get("status_code", "")
            ):
                missing.append(f"{method} (status={kwargs.get('status_code')}) {router_path.name}")

        assert not missing, (
            f"Los siguientes endpoints no tienen response_model=: {missing}. "
            "Toda ruta no-DELETE debe declarar response_model= como allowlist PII."
        )

    def test_campaigns_router_response_models(self) -> None:
        """campaigns_router.py — todos los endpoints tienen response_model=."""
        self._check_router_file(_ROUTERS_DIR / "campaigns_router.py")

    def test_segments_router_response_models(self) -> None:
        """segments_router.py — todos los endpoints tienen response_model=."""
        self._check_router_file(_ROUTERS_DIR / "segments_router.py")

    def test_templates_router_response_models(self) -> None:
        """templates_router.py — todos los endpoints tienen response_model=."""
        self._check_router_file(_ROUTERS_DIR / "templates_router.py")
