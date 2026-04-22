"""Mutation tools — allow the copilot to propose changes to form fields.

The tool emits a ``proposal`` ui_action that the frontend renders as a
confirmation card. The user must approve before anything is persisted.

# [COPILOT-MUTATION-VALIDATION] → docs/domains/copilot/editable-fields.md
Updates are validated against the editable-fields SSoT via
``src.shared.links.ports.editable_fields``. Invalid ``field_id``s are
rejected with structured feedback so the LLM can self-correct on the
next turn instead of pushing phantom fields to the FE.
"""

from __future__ import annotations

import structlog
from langchain_core.tools import tool

from src.shared.links.ports.editable_fields import get_paths_for, get_registered_domains

logger = structlog.get_logger()


def _guess_domain(field_id: str) -> str | None:
    """Infer the owning domain from ``field_id`` by probing registered catalogs.

    Multiple domains could in theory share a path, but today the catalogs
    do not overlap. We scan them deterministically and return the first
    match. If no domain claims the path, the update is rejected.
    """
    for domain in get_registered_domains():
        if field_id in get_paths_for(domain):
            return domain
    return None


@tool
def propose_field_updates(updates: list[dict]) -> dict:
    """Propón cambios a campos del formulario. El usuario debe aprobarlos.

    Args:
        updates: Lista de cambios. Cada elemento necesita:
            - ``field_id``: path canónico (ej. ``"identity.brand_name"``
              para brand, ``"public_name"`` para offer). Debe existir en
              el catálogo editable del copilot; si no, se rechaza.
            - ``new_value``: valor propuesto.
            - ``reason`` (opcional): breve justificación mostrada al usuario.

    Returns:
        Dict con:
            - ``success``: bool — True si al menos una propuesta pasa.
            - ``ui_action``: payload ``proposal`` cuando hay actualizaciones válidas.
            - ``rejected``: lista de ``{field_id, reason}`` para campos inválidos.
            - ``message``: resumen en español para el LLM.

    """
    validated: list[dict] = []
    rejected: list[dict] = []

    for u in updates:
        field_id = u.get("field_id")
        new_value = u.get("new_value")
        if not field_id or new_value is None:
            rejected.append(
                {
                    "field_id": str(field_id or ""),
                    "reason": "Faltan campos obligatorios: field_id y new_value.",
                },
            )
            continue

        domain = _guess_domain(str(field_id))
        if domain is None:
            # The LLM proposed a path that exists in no catalog. This is
            # the common failure mode after a schema change — surface it
            # clearly so the model tries a different path.
            known_domains = ", ".join(get_registered_domains())
            rejected.append(
                {
                    "field_id": field_id,
                    "reason": (
                        f"'{field_id}' no está en el catálogo editable. "
                        f"Dominios registrados: {known_domains}. "
                        "Usa `get_module_data` para ver los campos disponibles."
                    ),
                },
            )
            continue

        validated.append(
            {
                "field_id": field_id,
                "new_value": new_value,
                "reason": u.get("reason", ""),
                "domain": domain,
            },
        )

    if not validated:
        return {
            "success": False,
            "rejected": rejected,
            "message": (
                "Ninguna propuesta es válida. Revisa los `field_id` — deben "
                "aparecer exactamente en el catálogo editable. "
                f"Rechazados: {[r['field_id'] for r in rejected]}"
            ),
        }

    message = f"Propuesta de {len(validated)} cambio(s) enviada al usuario."
    if rejected:
        message += f" Se ignoraron {len(rejected)} field_id(s) inválido(s): {[r['field_id'] for r in rejected]}."

    return {
        "success": True,
        "ui_action": {
            "type": "proposal",
            "updates": [
                {"field_id": u["field_id"], "new_value": u["new_value"], "reason": u["reason"]} for u in validated
            ],
        },
        "rejected": rejected,
        "message": message,
    }


MUTATION_TOOLS = [propose_field_updates]
