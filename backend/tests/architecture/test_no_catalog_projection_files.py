"""Anti-regression: módulos migrados NO declaran su propio catalog file.

Post-Fase-08 los archivos ``copilot_editable_fields*.py`` de offer/brand/
buyer_persona fueron dropeados — boilerplate idéntico que ahora vive
una sola vez en ``shared/links/ports/editable_fields._derive_from_contracts``.

Re-introducir un archivo manual reabre la puerta al drift que la Fase
04/06/07 cerraron por construcción.

refs: docs/refactors/field-contract-platform/phases/08-copilot-unification/SPEC.md
"""

from __future__ import annotations

from pathlib import Path

MODULES_ROOT = Path(__file__).resolve().parents[2] / "src" / "modules"

MIGRATED_MODULES: tuple[str, ...] = ("offer", "brand", "buyer_persona")


class TestNoCatalogProjectionFiles:
    """Ningún módulo migrado declara archivos `copilot_editable_fields*.py`."""

    def test_no_copilot_editable_fields_files_exist(self) -> None:
        """Anti-regression del drop Fase 08."""
        forbidden_pattern = "copilot_editable_fields*.py"
        offenders: list[Path] = []
        for module in MIGRATED_MODULES:
            module_dir = MODULES_ROOT / module / "domain"
            if module_dir.exists():
                offenders.extend(module_dir.glob(forbidden_pattern))
            # Buyer persona aggregate vive bajo brand/domain — chequear ahí también.
            brand_domain = MODULES_ROOT / "brand" / "domain"
            if module == "buyer_persona" and brand_domain.exists():
                offenders.extend(brand_domain.glob("copilot_editable_fields_buyer_persona.py"))

        offenders = sorted({p.relative_to(MODULES_ROOT) for p in offenders})
        assert not offenders, (
            f"Found re-introduced catalog projection files: {offenders}.\n"
            "Catalogs derive from FieldContract registry via "
            "shared/links/ports/editable_fields._derive_from_contracts (Fase 08).\n"
            "Borralos y declara overrides en {module}/domain/field_contract.py."
        )

    def test_no_register_catalog_calls_in_module_domains(self) -> None:
        """Ningún archivo bajo modules/{m}/domain/ llama register_catalog.

        Post-Fase-08 register_catalog queda solo para test stubs. Los
        módulos migrados confían en la derivación automática del port.
        """
        offenders: list[str] = []
        for module in MIGRATED_MODULES:
            base = MODULES_ROOT / module / "domain"
            if not base.exists():
                continue
            for py in base.rglob("*.py"):
                content = py.read_text(encoding="utf-8")
                if "register_catalog(" in content:
                    offenders.append(str(py.relative_to(MODULES_ROOT)))
        # Buyer persona aggregate vive bajo brand/domain — ya cubierto por el iter brand.
        assert not offenders, (
            f"Module domain files calling register_catalog: {offenders}.\n"
            "Catalogs derive from FieldContract via shared port. "
            "register_catalog se reserva para test stubs únicamente."
        )
