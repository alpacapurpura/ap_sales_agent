"""Architectural fitness — SegmentFilter modelos Pydantic deben declarar extra='forbid'.

AST scan + introspección: cada clase en ``domain/segment_filter.py`` cuyo nombre
termina en ``Filter`` o ``Range`` o ``Filter`` subclase de ``BaseModel`` DEBE
declarar ``model_config = ConfigDict(extra="forbid")`` o ``extra='forbid'``.

Invariant: ``SegmentFilter`` (type alias) apunta a ``PredefinedSegmentFilter``.
Future ``ExpressiveSegmentFilter`` (vNext) también debe cumplir esta regla.

Rationale: el filter_dsl se persiste como JSONB y se deserializa en runtime.
Un filtro con campos desconocidos silenciosamente ignorados puede causar
evaluaciones incorrectas de segmento (enviar a leads que no corresponden).
``extra='forbid'`` convierte errores silenciosos en excepciones explícitas.

# [CAMPAIGNS-SEGMENT-FILTER-STRICT-PR3-S1]
"""

from __future__ import annotations

import ast
from pathlib import Path

import pydantic

REPO = Path(__file__).resolve().parents[2]
SEGMENT_FILTER_MODULE = REPO / "src" / "modules" / "campaigns" / "domain" / "segment_filter.py"


def _get_basemodel_subclasses_with_model_config(
    path: Path,
) -> list[tuple[str, bool]]:
    """Retorna list[(class_name, has_extra_forbid)] para clases BaseModel en el file."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    results: list[tuple[str, bool]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Solo clases que heredan de BaseModel (directa o indirecta).
        base_names = {
            b.id if isinstance(b, ast.Name) else (b.attr if isinstance(b, ast.Attribute) else "") for b in node.bases
        }
        if "BaseModel" not in base_names:
            continue
        has_forbid = _has_extra_forbid(node)
        results.append((node.name, has_forbid))

    return results


def _has_extra_forbid(class_def: ast.ClassDef) -> bool:
    """Verifica si una clase declara ``model_config = ConfigDict(extra='forbid')``."""
    for stmt in ast.walk(class_def):
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == "model_config" and isinstance(stmt.value, ast.Call):
                for kw in stmt.value.keywords:
                    if kw.arg == "extra" and isinstance(kw.value, ast.Constant) and kw.value.value == "forbid":
                        return True
    return False


class TestSegmentFilterPydanticStrict:
    """Verifica que todos los modelos SegmentFilter son Pydantic strict (extra=forbid)."""

    def test_segment_filter_module_exists(self) -> None:
        assert SEGMENT_FILTER_MODULE.exists(), f"segment_filter.py no encontrado: {SEGMENT_FILTER_MODULE}"

    def test_all_basemodel_subclasses_have_extra_forbid(self) -> None:
        """Toda clase BaseModel en segment_filter.py debe tener extra='forbid'."""
        classes = _get_basemodel_subclasses_with_model_config(SEGMENT_FILTER_MODULE)
        assert classes, "segment_filter.py debe contener al menos una clase BaseModel"

        violations: list[str] = []
        for class_name, has_forbid in classes:
            if not has_forbid:
                violations.append(class_name)

        assert not violations, (
            "Las siguientes clases SegmentFilter no declaran extra='forbid'. "
            "Esto es crítico: un filter_dsl con campos desconocidos ignorados "
            "puede causar segmentaciones incorrectas.\n"
            "Violations: " + ", ".join(violations)
        )

    def test_predefined_segment_filter_runtime_rejects_extra_fields(self) -> None:
        """Runtime check: PredefinedSegmentFilter rechaza campos desconocidos."""
        from luana_core_campaigns.domain.segment_filter import PredefinedSegmentFilter

        import pytest

        with pytest.raises(pydantic.ValidationError):
            PredefinedSegmentFilter(unknown_field="should_fail")  # type: ignore[call-arg]

    def test_segment_filter_alias_points_to_predefined(self) -> None:
        """SegmentFilter type alias debe apuntar a PredefinedSegmentFilter."""
        from luana_core_campaigns.domain.segment_filter import (
            PredefinedSegmentFilter,
            SegmentFilter,
        )

        assert SegmentFilter is PredefinedSegmentFilter, (
            "SegmentFilter type alias debe ser PredefinedSegmentFilter. "
            "Si se agrega ExpressiveSegmentFilter, usar Union[] y actualizar este test."
        )

    def test_score_range_extra_forbid(self) -> None:
        """ScoreRange también debe tener extra='forbid'."""
        from luana_core_campaigns.domain.segment_filter import ScoreRange

        import pytest

        with pytest.raises(pydantic.ValidationError):
            ScoreRange(unknown="fail")  # type: ignore[call-arg]

    def test_date_range_extra_forbid(self) -> None:
        """DateRange también debe tener extra='forbid'."""
        from luana_core_campaigns.domain.segment_filter import DateRange

        import pytest

        with pytest.raises(pydantic.ValidationError):
            DateRange(unknown="fail")  # type: ignore[call-arg]
