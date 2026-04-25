"""Social proof ``CopilotProvider`` — F1 shim.

Three roots (testimonials, authority items, team members) are bundled by the
``read_fn`` so consumers iterate the dict and fan out per collection — same
shape the legacy ``MODULE_REGISTRY`` produced.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src.modules.copilot.domain.ports import BaseCopilotProvider, ModuleData

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.social_proof.infrastructure.repositories.authority_item_repository import (
        AuthorityItemRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.team_member_repository import (
        TeamMemberRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
        TestimonialRepository,
    )


def _social_proof_repo_factory(db: object) -> object:
    from src.modules.social_proof.infrastructure.repositories.authority_item_repository import (
        AuthorityItemRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.team_member_repository import (
        TeamMemberRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
        TestimonialRepository,
    )

    return {
        "testimonials": TestimonialRepository(db),
        "authority_items": AuthorityItemRepository(db),
        "team_members": TeamMemberRepository(db),
    }


def _social_proof_read_fn(repo: object, tenant_id: UUID) -> dict:
    bundle = cast("dict", repo)
    testimonials_repo = cast("TestimonialRepository", bundle["testimonials"])
    authority_repo = cast("AuthorityItemRepository", bundle["authority_items"])
    team_repo = cast("TeamMemberRepository", bundle["team_members"])
    return {
        "testimonials": testimonials_repo.list_by_tenant(tenant_id),
        "authority_items": authority_repo.list_by_tenant(tenant_id),
        "team_members": team_repo.list_by_tenant(tenant_id),
    }


class SocialProofCopilotProvider(BaseCopilotProvider):
    """Social proof module surface for the copilot."""

    @property
    def module_id(self) -> str:
        return "social_proof"

    @property
    def label(self) -> str:
        return "Social Proof Studio"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="social_proof",
            label="Social Proof Studio",
            description=(
                "Prueba social tenant-scoped: testimonios de clientes, autoridades"
                " / certificaciones / premios, equipo (voz de marca). Se reutiliza"
                " cross-surface (brand, offer, landing, email, sales agent) via"
                " placements M:N — editar un testimonio se propaga automáticamente."
            ),
            route_prefix="social-proof",
            model_class=None,
            repo_factory=_social_proof_repo_factory,
            read_fn=_social_proof_read_fn,
            keywords=(
                "testimonios",
                "testimonio",
                "autoridad",
                "authority",
                "certificaciones",
                "equipo",
                "team",
                "prueba social",
                "confianza",
                "credibilidad",
            ),
        )
