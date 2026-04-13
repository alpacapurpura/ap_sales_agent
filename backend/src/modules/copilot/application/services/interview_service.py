"""Interview Engine orchestration service."""

# Ensure domain configs are registered on import
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

import src.modules.copilot.domain.interview_configs.brand_config  # noqa: F401
from src.modules.copilot.domain.interview_config import (
    DOMAIN_CONFIGS,
    get_interview_config,
)
from src.modules.copilot.domain.interview_session import (
    InterviewSession,
    InterviewStatus,
)
from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)
from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
    InterviewSessionRepository,
)

DOMAIN_LABELS = {
    "brand": "Brand Studio",
    "buyer_persona": "Buyer Persona",
    "offer": "Offer Studio",
}


class InterviewService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = InterviewSessionRepository(db)
        self.conversation_repo = ConversationRepository(db)

    def start_interview(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        domain: str,
        resume_session_id: UUID | None = None,
        entity_id: UUID | None = None,
        initial_mapa: dict | None = None,
    ) -> dict:
        if resume_session_id:
            session = self.session_repo.get_by_id(resume_session_id, tenant_id)
            if not session or session.status != InterviewStatus.PAUSED:
                msg = "Session not found or not paused"
                raise ValueError(msg)
            session.resume()
            self.session_repo.save(session)
            self.db.commit()
            return {
                "session_id": session.id,
                "conversation_id": session.conversation_id,
                "config": session.config_snapshot,
                "initial_message": (
                    f"¡Bienvenido de vuelta! Continuemos donde quedamos — estábamos en {session.bloque_actual}."
                ),
            }

        existing = self.session_repo.get_active_by_domain(tenant_id, domain)
        if existing:
            msg = "Active session exists for this domain"
            raise ValueError(msg)

        config = get_interview_config(domain)

        conversation_id = uuid4()
        self.conversation_repo.create(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=f"Entrevista {DOMAIN_LABELS.get(domain, domain)}",
        )

        session = InterviewSession.create(
            tenant_id=tenant_id,
            domain=domain,
            config=config,
            conversation_id=conversation_id,
            entity_id=entity_id,
            initial_mapa=initial_mapa,
        )
        self.session_repo.save(session)
        self.db.commit()

        return {
            "session_id": session.id,
            "conversation_id": session.conversation_id,
            "config": session.config_snapshot,
            "initial_message": (
                f"¡Hola! Vamos a construir tu {DOMAIN_LABELS.get(domain, 'proyecto')}"
                f" juntos. Cuéntame, ¿cómo nació tu negocio?"
            ),
        }

    def get_active(self, tenant_id: UUID) -> dict | None:
        for domain in DOMAIN_CONFIGS:
            session = self.session_repo.get_active_by_domain(tenant_id, domain)
            if session:
                config = session.config_snapshot
                return {
                    "session_id": session.id,
                    "domain": session.domain,
                    "domain_label": DOMAIN_LABELS.get(session.domain, session.domain),
                    "bloque_actual": session.bloque_actual,
                    "bloques_completados": session.bloques_completados,
                    "total_bloques": len(config.get("bloques", [])),
                }
        return None

    def get_state(self, session_id: UUID, tenant_id: UUID) -> dict | None:
        session = self.session_repo.get_by_id(session_id, tenant_id)
        if not session:
            return None
        return {
            "session_id": session.id,
            "mapa_global": session.mapa_global,
            "bloque_actual": session.bloque_actual,
            "bloques_completados": session.bloques_completados,
            "config": session.config_snapshot,
            "messages_count": session.messages_count,
        }

    def pause(self, session_id: UUID, tenant_id: UUID) -> bool:
        session = self.session_repo.get_by_id(session_id, tenant_id)
        if not session or session.status != InterviewStatus.ACTIVE:
            return False
        session.pause()
        self.session_repo.save(session)
        self.db.commit()
        return True

    def abandon(self, session_id: UUID, tenant_id: UUID) -> bool:
        session = self.session_repo.get_by_id(session_id, tenant_id)
        if not session or session.status not in (
            InterviewStatus.ACTIVE,
            InterviewStatus.PAUSED,
        ):
            return False
        session.abandon()
        self.session_repo.save(session)
        self.db.commit()
        return True

    def get_session(self, session_id: UUID, tenant_id: UUID) -> InterviewSession | None:
        """Retrieve a session by ID and tenant. Returns None if not found."""
        return self.session_repo.get_by_id(session_id, tenant_id)

    def update_mapa_global(
        self,
        *,
        session_id: UUID,
        tenant_id: UUID,
        delta: dict,
    ) -> None:
        """Merge delta into the session's mapa_global and persist."""
        session = self.session_repo.get_by_id(session_id, tenant_id)
        if not session:
            return
        session.update_mapa_global(delta)
        self.session_repo.save(session)
        self.db.commit()
