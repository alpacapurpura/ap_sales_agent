"""Interview Session domain entity."""

from __future__ import annotations

from dataclasses import asdict
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from src.modules.copilot.domain.interview_config import InterviewConfig


class InterviewStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewSession:
    """Represents an ongoing interview session with a tenant."""

    def __init__(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        domain: str,
        config_snapshot: dict,
        conversation_id: UUID,
        mapa_global: dict,
        bloque_actual: str,
        bloques_completados: list[str],
        status: InterviewStatus,
        messages_count: int,
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.domain = domain
        self.config_snapshot = config_snapshot
        self.conversation_id = conversation_id
        self.mapa_global = mapa_global
        self.bloque_actual = bloque_actual
        self.bloques_completados = bloques_completados
        self.status = status
        self.messages_count = messages_count

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        domain: str,
        config: InterviewConfig,
        conversation_id: UUID,
    ) -> InterviewSession:
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            domain=domain,
            config_snapshot=asdict(config),
            conversation_id=conversation_id,
            mapa_global={},
            bloque_actual=config.bloques[0].id,
            bloques_completados=[],
            status=InterviewStatus.ACTIVE,
            messages_count=0,
        )

    def advance_block(self, block_id: str) -> None:
        if block_id not in self.bloques_completados:
            self.bloques_completados.append(block_id)
        bloques = self.config_snapshot["bloques"]
        block_ids = [b["id"] for b in bloques]
        current_idx = block_ids.index(block_id)
        if current_idx + 1 >= len(block_ids):
            self.status = InterviewStatus.COMPLETED
            self.bloque_actual = ""
        else:
            self.bloque_actual = block_ids[current_idx + 1]

    def pause(self) -> None:
        self.status = InterviewStatus.PAUSED

    def resume(self) -> None:
        self.status = InterviewStatus.ACTIVE

    def abandon(self) -> None:
        self.status = InterviewStatus.ABANDONED

    def update_mapa_global(self, delta: dict) -> None:
        self.mapa_global.update(delta)

    def coverage_for_block(self, block_id: str) -> float:
        bloques = self.config_snapshot["bloques"]
        block = next((b for b in bloques if b["id"] == block_id), None)
        if not block:
            return 0.0
        campos = block["campos_objetivo"]
        if not campos:
            return 1.0
        filled = sum(1 for f in campos if self.mapa_global.get(f))
        return filled / len(campos)

    def increment_messages(self) -> None:
        self.messages_count += 1
