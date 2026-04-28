"""Architectural fitness: sales_agent -> module imports ratchet.

[SALES-AGENT-REDESIGN-2026-04 S6] -> docs/domains/sales-agent/redesign-2026-04/

Mirror del pattern ``test_no_new_copilot_module_imports.py``. Captura el set
actual de imports FROM ``src/modules/sales_agent/`` TO otros módulos de
dominio (excluyendo ``shared``, ``core``, ``iam`` y ``sales_agent`` mismo).

S6 congela el baseline post-S5 (sweep copilot shims completed). Cada fase
posterior que absorba dependencia adicional via port o evento de dominio
remueve la entrada — el ratchet sólo SHRINK.

Hoy ``sales_agent`` está en ``CROSS_IMPORT_ALLOWED_SOURCES`` de
``test_ddd_boundaries.py`` (orchestrator infra-like, igual que copilot).
Esa exención oculta el coupling real. Este test lo hace visible y lo
congela.

Cómo arreglar una violation
---------------------------
1. Mover la dependencia a un port en ``shared/links/ports/<target>.py``
   o emitir un evento de dominio que el target consuma.
2. Actualizar sales_agent para consumir el port.
3. Remover la entrada stale de ``KNOWN_SALES_AGENT_TO_MODULE_IMPORTS``.

Last verified baseline: 2026-04-28 (S6 close — 4 lazy imports a brand /
crm / offer son TYPE_CHECKING, candidatos a formalizar como ports
cuando S7+ promueva brand_voice + scheduler tools).
"""

from __future__ import annotations

import ast
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Ratchet state — frozen by S6 (April 2026).
# ──────────────────────────────────────────────────────────────────────────────
_RATCHET_FROZEN: bool = True

SALES_AGENT_DIR = Path(__file__).resolve().parents[2] / "src" / "modules" / "sales_agent"
MODULES_BASE = Path(__file__).resolve().parents[2] / "src" / "modules"

# Targets que sales_agent puede importar libremente (cross-cutting / infra).
ALLOWED_TARGETS: frozenset[str] = frozenset({"sales_agent", "shared", "core", "iam"})

# Provider-pattern: imports desde ``copilot_provider/`` al contract surface
# de copilot (``ports`` / ``workflow``) son la dependency-inversion knot.
# Mirror del exception en ``test_ddd_boundaries.py``.
_PROVIDER_CONTRACT_PREFIXES: frozenset[str] = frozenset(
    {
        "src.modules.copilot.domain.ports",
        "src.modules.copilot.domain.workflow",
    }
)


# ──────────────────────────────────────────────────────────────────────────────
# FROZEN BASELINE (4 entries) at S6 close (2026-04-28).
#
# Las 4 entradas son TYPE_CHECKING / lazy imports documentadas en
# ``audit/sales-agent-current-state.md §2 Outbound``. Son tolerables hoy:
#
# - ``style_anchor_retriever`` lee colección Qdrant brand → port `shared/
#   links/ports/brand.py` candidato cuando S7 promueva brand_voice
#   lighthouse.
# - ``channel_resolver`` y ``chat.py`` leen ``crm.LeadModel`` para identidad
#   del lead → port `shared/links/ports/crm_repos.py` ya existe parcialmente
#   pero estos imports anteceden al port. DEFERRED-post-S6 reemplazo total.
# - ``business_repository`` lee ``offer.ProductModel`` para catálogo de
#   ofertas. Port `shared/links/ports/offer.py` candidato.
#
# Las 4 son IRREDUCIBLES para S6 (scope estricto: ratchet + sweeps de S4/S5).
# ──────────────────────────────────────────────────────────────────────────────
KNOWN_SALES_AGENT_TO_MODULE_IMPORTS: frozenset[str] = frozenset(
    {
        "sales_agent -> brand | sales_agent/application/services/style_anchor_retriever.py",
        "sales_agent -> crm | sales_agent/application/orchestrator/chat.py",
        "sales_agent -> crm | sales_agent/application/services/channel_resolver.py",
        "sales_agent -> offer | sales_agent/infrastructure/db/repositories/business_repository.py",
    }
)


def _is_provider_contract_import(py_file_parts: tuple[str, ...], imported_module: str) -> bool:
    """Imports al copilot provider contract desde ``copilot_provider/`` son DI."""
    if "copilot_provider" not in py_file_parts:
        return False
    return any(
        imported_module == prefix or imported_module.startswith(f"{prefix}.") for prefix in _PROVIDER_CONTRACT_PREFIXES
    )


def _collect_sales_agent_to_module_imports() -> set[str]:
    """Walk sales_agent/ y produce ``'sales_agent -> {target} | {rel_path}'``
    para cada cross-module import a un target no permitido."""
    found: set[str] = set()
    for py in sorted(SALES_AGENT_DIR.rglob("*.py")):
        rel = py.relative_to(MODULES_BASE).as_posix()
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if not node.module.startswith("src.modules."):
                    continue
                target = node.module.split(".")[2]
                if target in ALLOWED_TARGETS:
                    continue
                if _is_provider_contract_import(py.parts, node.module):
                    continue
                found.add(f"sales_agent -> {target} | {rel}")
    return found


def test_no_new_sales_agent_to_module_imports() -> None:
    """sales_agent NO debe introducir nuevos cross-module imports más allá del baseline S6.

    Frozen by S6 (April 2026): cada nuevo ``sales_agent -> module`` debe
    pasar por un port en ``shared/links/ports/`` o un evento de dominio.
    El allowlist sólo SHRINK — agregar entradas requiere justificación
    documentada en la PR description y tech-debt-log.
    """

    assert _RATCHET_FROZEN, "S6 froze the ratchet — flip back requires explicit decision in commit."

    actual = _collect_sales_agent_to_module_imports()
    new_violations = sorted(actual - KNOWN_SALES_AGENT_TO_MODULE_IMPORTS)
    if new_violations:
        joined = "\n  ".join(new_violations)
        msg = (
            "Nuevos sales_agent -> module imports detectados. Reemplazar con un port "
            "en shared/links/ports/ (ver docs/domains/sales-agent/redesign-2026-04/"
            "02-architecture-target.md):"
            f"\n  {joined}"
        )
        raise AssertionError(msg)


def test_baseline_count_matches_documented_state() -> None:
    """Sanity guard del baseline documentado.

    Editar el frozen set sin actualizar el comentario count falla CI para
    que la intención de cada shrink/grow sea visible en review.
    """
    expected = 4
    assert len(KNOWN_SALES_AGENT_TO_MODULE_IMPORTS) == expected, (
        f"Frozen baseline editado sin actualizar el count comment: "
        f"esperado {expected}, encontrado {len(KNOWN_SALES_AGENT_TO_MODULE_IMPORTS)}."
    )


def test_stale_entries_do_not_grow() -> None:
    """Stale entries (frozen pero ya absorbidas) reportan pero no crashean.

    Diagnóstico útil cuando se hace shrink — mantiene ``_RATCHET_FROZEN = True``
    enforzando nuevas violations mientras señala líneas removibles.
    """
    actual = _collect_sales_agent_to_module_imports()
    stale = sorted(KNOWN_SALES_AGENT_TO_MODULE_IMPORTS - actual)
    assert isinstance(stale, list), "always passes; pretty-prints stale entries on demand"
