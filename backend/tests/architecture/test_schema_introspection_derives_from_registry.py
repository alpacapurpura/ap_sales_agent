"""Anti-regression: schema_introspection._build_*_paths derivan del registry.

Post-Fase-08 los 3 builders consumen ``get_module_contracts(domain)``
en lugar de:
- get_model_sections(BrandSettings) walk Pydantic
- PERSISTABLE_FIELDS (offer) — indirección
- top_level + dot_notation hand-authored set (buyer_persona)

Si alguien re-introduce literales de paths hand-authored, este test lo
detecta vía AST scan + behavioural assertion.

refs: docs/refactors/field-contract-platform/phases/08-copilot-unification/SPEC.md
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SCHEMA_INTROSPECTION_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "modules" / "copilot" / "domain" / "schema_introspection.py"
)

BUILDERS: tuple[str, ...] = (
    "_build_brand_paths",
    "_build_offer_paths",
    "_build_buyer_persona_paths",
)


def _builder_node(source: str, name: str) -> ast.FunctionDef:
    """Locate a top-level function definition by name in a parsed module."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    msg = f"function {name!r} not found in schema_introspection.py"
    raise AssertionError(msg)


class TestSchemaIntrospectionDerivesFromRegistry:
    """Los 3 builders consumen get_module_contracts en su cuerpo."""

    @pytest.mark.parametrize("builder", BUILDERS)
    def test_builder_calls_get_module_contracts(self, builder: str) -> None:
        """AST scan: cada builder invoca ``get_module_contracts(...)``."""
        source = SCHEMA_INTROSPECTION_PATH.read_text(encoding="utf-8")
        node = _builder_node(source, builder)

        calls = [
            n
            for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "get_module_contracts"
        ]
        assert calls, (
            f"{builder} no invoca get_module_contracts. Post-Fase-08 cada "
            "builder deriva del FieldContract registry directo."
        )

    @pytest.mark.parametrize("builder", BUILDERS)
    def test_builder_has_no_inline_path_literal_set(self, builder: str) -> None:
        """AST scan: los builders no declaran sets literales con > 5 strings.

        Post-Fase-08 los paths son derivados, no listados. Un set literal
        grande es smoke de hand-authored hardcoding (ej: el viejo
        ``top_level = {"name", "tagline", "pain_points", ...}`` que la
        Fase 08 cerró).
        """
        source = SCHEMA_INTROSPECTION_PATH.read_text(encoding="utf-8")
        node = _builder_node(source, builder)

        offenders: list[ast.Set] = []
        for n in ast.walk(node):
            if not isinstance(n, ast.Set):
                continue
            string_elts = [e for e in n.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if len(string_elts) > 5:
                offenders.append(n)

        assert not offenders, (
            f"{builder} declara un set literal con >5 paths string. "
            "Post-Fase-08 los paths derivan del FieldContract registry. "
            "Si necesitás un legacy patch, agregálo al registry, no al builder."
        )

    def test_buyer_persona_dict_parents_derived_from_subkeys(self) -> None:
        """``_DOMAIN_DICT_PARENTS["buyer_persona"]`` deriva de BUYER_PERSONA_DICT_SUBKEYS.keys()."""
        from luana_core_brand_studio.domain.buyer_persona_field_contract import (
            BUYER_PERSONA_DICT_SUBKEYS,
        )
        from luana_core_copilot.domain.schema_introspection import _get_dict_parents

        actual = _get_dict_parents("buyer_persona")
        expected = set(BUYER_PERSONA_DICT_SUBKEYS.keys())
        assert actual == expected, (
            f"_get_dict_parents('buyer_persona') diverged from "
            f"BUYER_PERSONA_DICT_SUBKEYS.keys().\n"
            f"Actual: {sorted(actual)}\nExpected: {sorted(expected)}"
        )

    def test_unknown_domain_dict_parents_empty(self) -> None:
        """Dominios sin dict_parents devuelven set vacío."""
        from luana_core_copilot.domain.schema_introspection import _get_dict_parents

        assert _get_dict_parents("offer") == set()
        assert _get_dict_parents("brand") == set()
        assert _get_dict_parents("nonexistent") == set()
