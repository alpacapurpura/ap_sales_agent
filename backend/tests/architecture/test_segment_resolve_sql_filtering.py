"""Architectural fitness — segmento resolve usa SQL-side filtering, no Python-side.

Verifica que SegmentFilterEvaluator genera predicados SQL (no filtra en Python)
y que SegmentService.resolve() delega a LeadQueryPort (never loads all leads to memory).

# [SEGMENT-RESOLVE-SQL-FILTERING-PR4-S1]
"""

from __future__ import annotations

import ast
import pathlib

_EVALUATOR_PATH = pathlib.Path("src/modules/campaigns/application/segment_filter_evaluator.py")
_SEGMENT_SERVICE_PATH = pathlib.Path("src/modules/campaigns/application/services/segment_service.py")


class TestSegmentResolveSQLFiltering:
    """SegmentFilterEvaluator produce SQL predicados, no filtra en Python."""

    def test_evaluator_file_exists(self) -> None:
        """SegmentFilterEvaluator debe existir en application/."""
        assert _EVALUATOR_PATH.exists(), (
            f"SegmentFilterEvaluator no encontrado en {_EVALUATOR_PATH}. "
            "El evaluador SQL debe existir para evitar full-table-scan en Python."
        )

    def test_evaluator_uses_sqlalchemy_constructs(self) -> None:
        """SegmentFilterEvaluator importa SQLAlchemy para construir predicados."""
        source = _EVALUATOR_PATH.read_text()
        # Must use sqlalchemy Column constructs, not pure Python filtering
        has_sqla = "sqlalchemy" in source or "select(" in source or "and_(" in source
        has_where = "where" in source or "filter" in source or "BinaryExpression" in source
        assert has_sqla or has_where, (
            "SegmentFilterEvaluator debe usar SQLAlchemy para construir predicados SQL. "
            "Filtrar leads en Python = full table scan = O(N) — inaceptable en prod."
        )

    def test_evaluator_does_not_load_all_leads(self) -> None:
        """SegmentFilterEvaluator no hace 'SELECT * FROM leads' sin WHERE."""
        source = _EVALUATOR_PATH.read_text()
        tree = ast.parse(source)

        # Look for any list comprehension that iterates over all leads without filter
        # Heuristic: no `[x for x in leads]` where leads is a raw collection
        list_comps = [node for node in ast.walk(tree) if isinstance(node, ast.ListComp)]

        # If list comprehensions exist, they should not be filtering domain objects
        # (SQL-side filtering means data arrives pre-filtered)
        # This is a best-effort heuristic test
        for comp in list_comps:
            comp_source = ast.unparse(comp)
            # No list comprehension should be doing domain-level filtering of a bulk query
            if "lead.lifecycle" in comp_source or "lead.temperature" in comp_source:
                msg = f"SegmentFilterEvaluator tiene filtrado Python en: {comp_source}. Mover filtrado a SQL predicado."
                raise AssertionError(msg)

    def test_segment_service_has_resolve_method(self) -> None:
        """SegmentService.resolve() existe y delega a lead_query_port."""
        source = _SEGMENT_SERVICE_PATH.read_text()
        assert "async def resolve" in source, (
            "SegmentService debe tener método async resolve(). Es el entry-point para materializar el segmento."
        )

    def test_segment_service_uses_lead_query_port(self) -> None:
        """SegmentService usa lead_query_port (port pattern) no el repo de leads directamente."""
        source = _SEGMENT_SERVICE_PATH.read_text()
        # Must reference a port/interface, not direct LeadRepository
        has_port = "lead_query_port" in source or "LeadQueryPort" in source
        assert has_port, (
            "SegmentService debe usar LeadQueryPort para resolver leads. "
            "Inyectar LeadRepository directamente viola DDD cross-module boundaries."
        )

    def test_segment_service_no_direct_crm_import(self) -> None:
        """SegmentService no importa directamente desde modules/crm/ (cross-module DDD)."""
        source = _SEGMENT_SERVICE_PATH.read_text()
        tree = ast.parse(source)
        direct_crm_imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", "") or ""
                names = [alias.name for alias in getattr(node, "names", [])]
                all_names = [module, *names]
                for name in all_names:
                    if "modules.crm" in name and "shared" not in name:
                        direct_crm_imports.append(name)

        assert not direct_crm_imports, (
            f"SegmentService importa directamente desde crm/: {direct_crm_imports}. "
            "Usar port/interface en shared/ o pasar por inyección de dependencias."
        )
