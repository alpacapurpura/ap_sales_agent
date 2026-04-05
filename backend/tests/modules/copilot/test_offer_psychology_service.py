from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.application.services.offer_psychology_service import (
    CopilotOfferPsychologyService,
)
from src.modules.copilot.infrastructure.prompts.base import prompt_loader
from src.modules.offer.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)


@pytest.mark.asyncio
async def test_generate_psychology_success():
    request = PsychologyGenerationRequest(
        avatar_id=uuid4(),
        offer_name="Mentoría Premium",
        offer_description="Acompañamiento para escalar ventas",
        current_pains=["no cierro ventas"],
        current_desires=["ingresos estables"],
    )
    tenant_id = uuid4()
    avatar = SimpleNamespace(
        name="Founder Fit",
        icp_description="Dueña de negocio digital",
        tenant_id=tenant_id,
    )

    service = CopilotOfferPsychologyService(MagicMock())
    service.avatar_repo = MagicMock()
    service.avatar_repo.get_by_id.return_value = avatar

    with (
        patch(
            "src.modules.copilot.application.services.offer_psychology_service.prompt_loader.render",
            return_value="PROMPT_RENDERED",
        ) as render_mock,
        patch(
            "src.modules.copilot.application.services.offer_psychology_service.AIActionService.run_structured_action"
        ) as run_structured_action_mock,
    ):
        run_structured_action_mock.return_value = PsychologyGenerationResponse(
            pains=["p1", "p2", "p3", "p4", "p5"],
            desires=["d1", "d2", "d3", "d4", "d5"],
        )

        response = await service.generate_psychology(request, tenant_id)

    assert response.pains[0] == "p1"
    assert response.desires[0] == "d1"
    render_mock.assert_called_once()
    assert (
        render_mock.call_args.kwargs["template_name"] == "offer_psychology_generator.j2"
    )


@pytest.mark.asyncio
async def test_generate_psychology_avatar_not_found():
    request = PsychologyGenerationRequest(
        avatar_id=uuid4(),
        offer_name="Oferta X",
        offer_description=None,
        current_pains=[],
        current_desires=[],
    )
    service = CopilotOfferPsychologyService(MagicMock())
    service.avatar_repo = MagicMock()
    service.avatar_repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await service.generate_psychology(request, uuid4())


@pytest.mark.asyncio
async def test_generate_psychology_tenant_isolation():
    request = PsychologyGenerationRequest(
        avatar_id=uuid4(),
        offer_name="Oferta X",
        offer_description=None,
        current_pains=[],
        current_desires=[],
    )
    avatar = SimpleNamespace(
        name="Avatar",
        icp_description="Desc",
        tenant_id=uuid4(),
    )

    service = CopilotOfferPsychologyService(MagicMock())
    service.avatar_repo = MagicMock()
    service.avatar_repo.get_by_id.return_value = avatar

    with pytest.raises(ValueError, match="this tenant"):
        await service.generate_psychology(request, uuid4())


def test_offer_psychology_prompt_resolves_from_copilot_templates():
    with patch(
        "src.shared.infrastructure.prompts.base.settings.PROMPT_SOURCE",
        "file",
    ):
        rendered = prompt_loader.render(
            template_name="offer_psychology_generator.j2",
            avatar_name="A",
            avatar_description="B",
            avatar_pains="C",
            avatar_desires="D",
            offer_name="E",
            offer_description="F",
            current_pains="G",
            current_desires="H",
        )
    assert "Producto/Oferta: E" in rendered
