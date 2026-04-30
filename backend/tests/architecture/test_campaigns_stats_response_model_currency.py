"""Invariantes arquitecturales para el endpoint stats de campaigns (PR-8).

Sub-D: verifica que el endpoint declara response_model, que el DTO tiene
currency, que el servicio recibe tenant_id, y que el port existe.

KNOWN_CROSS_MODULE_TABLE_READS allowlist: count_responded_leads lee
sales_agent.messages desde campaigns — excepción documentada PR-8.
Justificación: lectura read-only tenant-scoped, overhead de port no
amortizado para un solo query (decisión arquitecto PR-8 §1).
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _read(rel: str) -> str:
    """Leer un archivo relativo al root del backend."""
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


# ── Allowlist cross-module table reads (ratchet — solo crece con justificación) ──


KNOWN_CROSS_MODULE_TABLE_READS = {
    # PR-8 §1: CampaignStatsService.count_responded_leads lee messages (sales_agent)
    # desde el repositorio de campaigns. Read-only, tenant-scoped. Documentado en
    # CampaignTaskRepository.count_responded_leads docstring.
    "count_responded_leads_reads_sales_agent_messages",
}


def test_known_cross_module_reads_not_grown() -> None:
    """KNOWN_CROSS_MODULE_TABLE_READS solo puede crecer con justificación documentada.

    Si este test falla tras un PR, DEBES agregar la justificación en este allowlist
    Y en el docstring del método que hace la lectura cruzada.
    """
    assert len(KNOWN_CROSS_MODULE_TABLE_READS) == 1, (
        "KNOWN_CROSS_MODULE_TABLE_READS tiene "
        f"{len(KNOWN_CROSS_MODULE_TABLE_READS)} entradas. "
        "Agregar nueva entrada requiere justificación en docstring del método."
    )


# ── Endpoint contract ─────────────────────────────────────────────────────────


def test_campaign_stats_response_declares_response_model() -> None:
    """El endpoint GET /{campaign_id}/stats DEBE declarar response_model=CampaignStatsResponse."""
    src = _read("src/modules/campaigns/api/routers/campaigns_router.py")
    assert "response_model=CampaignStatsResponse" in src, (
        "PR-8 contract: GET /campaigns/{id}/stats DEBE declarar "
        "response_model=CampaignStatsResponse (PII allowlist via pii-sanitisation.md)"
    )


# ── DTO invariants ────────────────────────────────────────────────────────────


def test_campaign_stats_response_has_currency_field() -> None:
    """CampaignStatsResponse debe tener campo currency: str | None (master-data invariante)."""
    src = _read("src/modules/campaigns/application/dtos/campaign_dtos.py")
    tree = ast.parse(src)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CampaignStatsResponse":
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and getattr(stmt.target, "id", None) == "currency":
                    found = True
                    break
    assert found, (
        "PR-8 master-data invariant: CampaignStatsResponse.currency: str | None REQUERIDO. "
        "Permite que PR-followup agregue revenue_total sin breaking change."
    )


def test_campaign_stats_response_has_attribution_method() -> None:
    """CampaignStatsResponse debe tener converted_count_attribution_method."""
    src = _read("src/modules/campaigns/application/dtos/campaign_dtos.py")
    assert "converted_count_attribution_method" in src, (
        "PR-8: CampaignStatsResponse debe documentar método de atribución MVP"
    )


def test_campaign_stats_response_has_rates() -> None:
    """CampaignStatsResponse debe tener response_rate y conversion_rate."""
    src = _read("src/modules/campaigns/application/dtos/campaign_dtos.py")
    assert "response_rate" in src, "CampaignStatsResponse debe tener response_rate"
    assert "conversion_rate" in src, "CampaignStatsResponse debe tener conversion_rate"


# ── Service tenant isolation ──────────────────────────────────────────────────


def test_campaign_stats_service_filters_tenant_id() -> None:
    """CampaignStatsService.get_stats debe recibir tenant_id (aislamiento de tenant)."""
    src = _read("src/modules/campaigns/application/services/campaign_stats_service.py")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_stats":
            arg_names = {a.arg for a in node.args.args} | {kw.arg for kw in node.args.kwonlyargs}
            assert "tenant_id" in arg_names, (
                "PR-8 tenant-isolation invariant: CampaignStatsService.get_stats DEBE recibir tenant_id como parámetro"
            )
            return
    msg = "CampaignStatsService.get_stats no encontrado en campaign_stats_service.py"
    raise AssertionError(msg)


# ── Port existence ────────────────────────────────────────────────────────────


def test_campaigns_lookup_port_exists() -> None:
    """shared/links/ports/campaigns.py debe exportar CampaignsLookupPort."""
    src = _read("src/shared/links/ports/campaigns.py")
    assert "class CampaignsLookupPort" in src, (
        "PR-8: CampaignsLookupPort debe existir en shared/links/ports/campaigns.py"
    )


def test_campaigns_lookup_port_has_required_methods() -> None:
    """CampaignsLookupPort debe tener los métodos requeridos para inbound + inbox."""
    src = _read("src/shared/links/ports/campaigns.py")
    assert "find_recent_campaign_task_for_lead" in src, (
        "CampaignsLookupPort debe tener find_recent_campaign_task_for_lead"
    )
    assert "find_recent_campaign_tasks_for_leads" in src, (
        "CampaignsLookupPort debe tener find_recent_campaign_tasks_for_leads (batch)"
    )


def test_create_campaigns_lookup_port_factory_exists() -> None:
    """La factory create_campaigns_lookup_port debe existir en el port."""
    src = _read("src/shared/links/ports/campaigns.py")
    assert "create_campaigns_lookup_port" in src, "PR-8: factory create_campaigns_lookup_port debe existir en el port"


# ── Inbound recognition ───────────────────────────────────────────────────────


def test_inbound_recognition_in_chat_orchestrator() -> None:
    """chat.py debe contener el bloque de reconocimiento inbound de campaña."""
    src = _read("src/modules/sales_agent/application/orchestrator/chat.py")
    assert "inbound_campaign" in src, "PR-8: chat.py debe contener el bloque inbound_campaign de reconocimiento"


def test_outbound_mode_false_during_inbound_recognition() -> None:
    """chat.py no debe activar outbound_mode=True durante reconocimiento inbound."""
    src = _read("src/modules/sales_agent/application/orchestrator/chat.py")
    assert "inbound_campaign" in src, "bloque inbound debe existir"

    # El bloque de reconocimiento inbound no debe asignar outbound_mode=True
    inbound_start = src.find("inbound_campaign")
    vicinity = src[max(0, inbound_start - 200) : inbound_start + 600]
    assert "outbound_mode=True" not in vicinity, (
        "outbound_mode NO debe activarse durante reconocimiento inbound "
        "(cache slot 7 debe quedar ausente — invariante PR-8 §8.1)"
    )


# ── ConversationListItem / Detail enrichment DTOs ─────────────────────────────


def test_conversation_list_item_has_campaign_fields() -> None:
    """ConversationListItem debe tener campaign_id y campaign_name opcionales."""
    src = _read("src/modules/sales_agent/api/dto/closer_studio.py")
    assert "campaign_id" in src, "ConversationListItem debe tener campo campaign_id"
    assert "campaign_name" in src, "ConversationListItem debe tener campo campaign_name"


def test_inbox_enrichment_service_exists() -> None:
    """inbox_campaign_enrichment.py debe existir con las funciones correctas."""
    svc_path = REPO_ROOT / "src/modules/sales_agent/application/services/inbox_campaign_enrichment.py"
    assert svc_path.exists(), "PR-8: inbox_campaign_enrichment.py debe existir en sales_agent/application/services/"
    src = svc_path.read_text(encoding="utf-8")
    assert "enrich_conversation_list_with_campaign" in src
    assert "enrich_conversation_detail_with_campaign" in src
