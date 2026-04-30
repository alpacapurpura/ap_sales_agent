"""Architectural fitness — campaigns FSM lógica en service layer, no en API.

Verifica que los routers de campaigns son thin (validate → service → map exception)
y que la lógica de transición FSM vive en CampaignService / Campaign aggregate,
NO en el router.

# [CAMPAIGNS-FSM-SERVICE-LAYER-PR4-S1]
"""

from __future__ import annotations

import ast
import pathlib

_ROUTER_PATH = pathlib.Path("src/modules/campaigns/api/routers/campaigns_router.py")
_SERVICE_PATH = pathlib.Path("src/modules/campaigns/application/services/campaign_service.py")


def _has_forbidden_patterns_in_router(source: str) -> list[str]:
    """Busca patrones de lógica de negocio en el router que deberían estar en el service."""
    forbidden = [
        "_FSM_TRANSITIONS",
        "transition_allowed",
        "CampaignStatus.RUNNING",
        "CampaignStatus.COMPLETED",
        "CampaignStatus.PAUSED",
        "CampaignStatus.SCHEDULED",
        "CampaignStatus.CANCELED",
    ]
    found = []
    for pattern in forbidden:
        if pattern in source:
            found.append(pattern)
    return found


class TestCampaignsFSMServiceLayer:
    """El router es thin — no contiene lógica FSM."""

    def test_router_has_no_fsm_transitions_access(self) -> None:
        """campaigns_router.py no importa ni usa _FSM_TRANSITIONS directamente."""
        source = _ROUTER_PATH.read_text()
        assert "_FSM_TRANSITIONS" not in source, (
            "El router no debe acceder a _FSM_TRANSITIONS. "
            "La lógica de transición FSM vive en CampaignService / Campaign aggregate."
        )

    def test_router_has_no_status_assignment(self) -> None:
        """El router no asigna status directamente — lo hace el service."""
        source = _ROUTER_PATH.read_text()
        # No direct status mutations in router
        assert ".status =" not in source, "El router no debe mutar .status directamente. Delegate al CampaignService."

    def test_service_has_fsm_transition_methods(self) -> None:
        """CampaignService expone métodos FSM: launch, cancel, pause, resume, complete."""
        source = _SERVICE_PATH.read_text()
        required_methods = ["launch", "cancel", "pause", "resume", "complete"]
        for method in required_methods:
            assert f"async def {method}" in source, (
                f"CampaignService debe tener método async {method}(). "
                "Toda transición FSM expuesta en el router debe tener método correspondiente."
            )

    def test_router_delegates_to_service(self) -> None:
        """Cada handler de FSM en el router llama svc.{method}(...) o orchestrator.{method}(...).

        launch() es manejado por CampaignOrchestrator (PI-1 S2 PR-5) que es el service
        layer real para lanzamiento. Los demás FSM transitions siguen en CampaignService.
        """
        source = _ROUTER_PATH.read_text()
        # launch: delegated to orchestrator (CampaignOrchestrator.launch()) — PR-5 PI-1 S2
        launch_delegated = "orchestrator.launch(" in source or "svc.launch(" in source
        assert launch_delegated, (
            "El router debe delegar launch() a orchestrator.launch() o svc.launch(). "
            "La lógica de lanzamiento vive en CampaignOrchestrator (PR-5 PI-1 S2)."
        )
        # Remaining FSM transitions: must go through CampaignService
        required_service_calls = ["svc.cancel(", "svc.pause(", "svc.resume(", "svc.complete("]
        missing = [call for call in required_service_calls if call not in source]
        assert not missing, (
            f"El router no delega al service para: {missing}. Cada transición FSM debe pasar por el service."
        )

    def test_router_maps_exceptions_to_http(self) -> None:
        """El router mapea excepciones de dominio a HTTPException, no las re-lanza raw."""
        source = _ROUTER_PATH.read_text()
        # Verify exception mapping exists
        assert "_CAMPAIGN_ERROR_MAP" in source or "_map_campaign_error" in source, (
            "El router debe tener mapeo de excepciones de dominio → HTTP. "
            "Usar _map_campaign_error o _CAMPAIGN_ERROR_MAP."
        )
        # Verify FastAPI HTTPException is used
        assert "HTTPException" in source, "El router debe levantar HTTPException, no excepciones de dominio crudas."

    def test_campaign_service_is_class_not_function(self) -> None:
        """CampaignService es una clase (no funciones sueltas)."""
        source = _SERVICE_PATH.read_text()
        tree = ast.parse(source)
        service_classes = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and "CampaignService" in node.name
        ]
        assert "CampaignService" in service_classes, (
            "CampaignService debe ser una clase. No funciones sueltas en la capa de aplicación."
        )
