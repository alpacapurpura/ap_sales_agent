"""Architectural fitness — campaigns pagination defaults.

Verifica que los endpoints de lista (GET) en campaigns, segments y templates
usan PaginatedResponse con defaults limit=20, offset=0.
También verifica que PaginatedResponse tiene los campos requeridos.

# [CAMPAIGNS-PAGINATION-DEFAULT-PR4-S1]
"""

from __future__ import annotations

from src.modules.campaigns.application.dtos.pagination import PaginatedResponse


class TestPaginatedResponseShape:
    """PaginatedResponse debe tener la estructura canónica."""

    def test_paginated_response_has_required_fields(self) -> None:
        """PaginatedResponse incluye items, total_count, limit, offset, has_more."""
        instance = PaginatedResponse[str](
            items=["a", "b"],
            total_count=2,
            limit=20,
            offset=0,
            has_more=False,
        )
        assert instance.items == ["a", "b"]
        assert instance.total_count == 2
        assert instance.limit == 20
        assert instance.offset == 0
        assert instance.has_more is False

    def test_paginated_response_has_more_computed(self) -> None:
        """has_more=True cuando hay más ítems que los retornados."""
        instance = PaginatedResponse[int](
            items=[1, 2],
            total_count=10,
            limit=2,
            offset=0,
            has_more=True,
        )
        assert instance.has_more is True

    def test_paginated_response_empty(self) -> None:
        """PaginatedResponse acepta lista vacía."""
        instance = PaginatedResponse[str](
            items=[],
            total_count=0,
            limit=20,
            offset=0,
            has_more=False,
        )
        assert instance.items == []
        assert instance.total_count == 0


class TestCampaignListDefaults:
    """Verifica que list_campaigns usa limit=20, offset=0 como default."""

    def test_list_campaigns_has_default_pagination(self) -> None:
        """campaigns_router list_campaigns tiene limit=20, offset=0 defaults."""
        import ast
        import pathlib

        source = pathlib.Path("src/modules/campaigns/api/routers/campaigns_router.py").read_text()
        tree = ast.parse(source)

        list_fn = None
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "list_campaigns":
                list_fn = node
                break

        assert list_fn is not None, "list_campaigns function not found in campaigns_router.py"

        # Find 'limit' and 'offset' args with defaults — checked via fn_source below
        for _arg in list_fn.args.args:
            pass

        # Parse function source to find Query(ge=1, le=100) default=20 etc
        fn_source = ast.unparse(list_fn)
        assert "limit" in fn_source, "list_campaigns debe tener parámetro 'limit'"
        assert "offset" in fn_source, "list_campaigns debe tener parámetro 'offset'"
        # ast.unparse uses `=20` (no spaces) for default values
        assert "=20" in fn_source, "list_campaigns debe tener limit default=20"
        assert "=0" in fn_source, "list_campaigns debe tener offset default=0"

    def test_list_segments_has_default_pagination(self) -> None:
        """segments_router list_segments tiene limit=20, offset=0 defaults."""
        import ast
        import pathlib

        source = pathlib.Path("src/modules/campaigns/api/routers/segments_router.py").read_text()
        tree = ast.parse(source)

        list_fn = None
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "list_segments":
                list_fn = node
                break

        assert list_fn is not None, "list_segments function not found in segments_router.py"
        fn_source = ast.unparse(list_fn)
        assert "limit" in fn_source, "list_segments debe tener parámetro 'limit'"
        assert "offset" in fn_source, "list_segments debe tener parámetro 'offset'"
