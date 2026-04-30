"""SalesAgentSuggestionProvider — heuristic, route-scoped, tenant-isolated.

Reads sales pipeline observability via ``shared/links/ports/sales_agent.py``
(NEW PR-2 port — keeps F1 ratchet ``copilot -> sales_agent`` at 0 entries).

§3 protected: this provider is READ-ONLY on enrollments + messages tables.
NEVER touches Closer Studio API/WS, BufferService, OutputManager, FollowUp,
PromptVersionModel, agent_state_checkpoint.

Heuristic rules (D-4, 5 reglas):
 1. count_leads_since(now-7d) == 0           -> "Sin leads esta semana"     (0.88)
 2. inactive_24h + leads_30d > 0             -> "Reactiva conversaciones"   (0.85)
 3. PersonalityProfile activo ausente        -> "Configura voz del agente"  (0.83)
 4. pending_payments_count > 0               -> "Cobros pendientes"         (0.80)
 5. waitlist_count > 0 + no_active_edition   -> "Lista de espera sin edición" (0.78)

[COPILOT-SUGGESTIONS-ENGINE] -> docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

import structlog

from src.core.database import SessionLocal
from src.modules.copilot.domain.suggestion import (
    Suggestion,
    SuggestionCategory,
    SuggestionContext,
)
from src.shared.links.ports.brand import create_brand_data_port
from src.shared.links.ports.sales_agent import create_sales_agent_observability_port

logger = structlog.get_logger()

_PAYMENT_PENDING_STATUS = "payment_pending"
_WAITLIST_STATUS = "waitlist"


class SalesAgentSuggestionProvider:
    """Heuristic suggestions for the Sales route."""

    @property
    def provider_id(self) -> str:
        """Stable id matching the module slug."""
        return "sales_agent"

    @property
    def provider_priority(self) -> int:
        """Tie-break weight. 10 = same level as brand (route-scoped)."""
        return 10

    @property
    def applies_to_routes(self) -> tuple[str, ...]:
        """Activate only on Sales routes."""
        return ("sales",)

    def get_suggestions(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int = 5,
    ) -> list[Suggestion]:
        """Compute heuristic suggestions. MUST NOT raise — returns [] on any error."""
        try:
            return self._compute(ctx, max_per_provider=max_per_provider)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "sales_agent_suggestion_provider_failed",
                tenant_id=str(ctx.tenant_id),
                error=str(exc),
            )
            return []

    def _compute(
        self,
        ctx: SuggestionContext,
        *,
        max_per_provider: int,
    ) -> list[Suggestion]:
        db = SessionLocal()
        try:
            sa_port = create_sales_agent_observability_port(db)
            brand_port = create_brand_data_port(db)

            now = datetime.now(tz=timezone.utc)
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            one_day_ago = now - timedelta(hours=24)

            suggestions: list[Suggestion] = []

            # Rule 1 — no leads in last 7 days
            leads_7d = self._safe_int(
                lambda: sa_port.count_leads_since(ctx.tenant_id, seven_days_ago),
                context="count_leads_7d",
            )
            if leads_7d == 0:
                suggestions.append(
                    Suggestion(
                        label="Sin leads esta semana",
                        prompt=("No tengo leads nuevos esta semana. ¿Cómo puedo activar canales de captación?"),
                        confidence=0.88,
                        category=SuggestionCategory.ACTION,
                        source_module="sales_agent",
                    )
                )

            # Rule 2 — no active conversations in 24h but old leads exist (>30d)
            active_24h = self._safe_int(
                lambda: sa_port.count_active_conversations_since(ctx.tenant_id, one_day_ago),
                context="count_active_24h",
            )
            leads_30d = self._safe_int(
                lambda: sa_port.count_leads_since(ctx.tenant_id, thirty_days_ago),
                context="count_leads_30d",
            )
            if active_24h == 0 and leads_30d > 0:
                suggestions.append(
                    Suggestion(
                        label="Reactiva conversaciones inactivas",
                        prompt=("Tengo leads sin actividad reciente. Ayúdame a definir una secuencia de reactivación."),
                        confidence=0.85,
                        category=SuggestionCategory.ACTION,
                        source_module="sales_agent",
                    )
                )

            # Rule 3 — no active personality profile (voice not configured)
            personality_present = self._safe_bool(
                lambda: brand_port.get_active_personality_profile_present(ctx.tenant_id),
                context="personality_profile_check",
            )
            if not personality_present:
                suggestions.append(
                    Suggestion(
                        label="Configura la voz del sales agent",
                        prompt=(
                            "El sales agent no tiene perfil de personalidad. Llévame al Brand Studio a configurarlo."
                        ),
                        confidence=0.83,
                        category=SuggestionCategory.NAV,
                        source_module="sales_agent",
                    )
                )

            # Rule 4 — pending payments older than 24h
            pending_enrollments = self._safe_list(
                lambda: sa_port.list_enrollments_by_status(
                    ctx.tenant_id,
                    statuses=(_PAYMENT_PENDING_STATUS,),
                ),
                context="pending_payments",
            )
            pending_old = [
                e
                for e in pending_enrollments
                if self._is_older_than_24h(e.created_at_iso, now)  # type: ignore[attr-defined]
            ]
            if pending_old:
                n = len(pending_old)
                suggestions.append(
                    Suggestion(
                        label="Cobros pendientes acumulados",
                        prompt=(
                            f"Tengo {n} enrollment{'s' if n > 1 else ''} con pago pendiente. "
                            "Revisemos qué hacer con cada uno."
                        ),
                        confidence=0.80,
                        category=SuggestionCategory.CLARIFY,
                        source_module="sales_agent",
                    )
                )

            # Rule 5 — waitlist enrollments exist but no active edition for their offer
            waitlist_enrollments = self._safe_list(
                lambda: sa_port.list_enrollments_by_status(
                    ctx.tenant_id,
                    statuses=(_WAITLIST_STATUS,),
                ),
                context="waitlist_check",
            )
            if waitlist_enrollments:
                # Check if at least one waitlist enrollment's offer has no active edition
                has_unmet_waitlist = False
                from uuid import UUID as _UUID

                for enrollment in waitlist_enrollments[:10]:  # cap for performance
                    try:
                        offer_id = _UUID(enrollment.offer_id)  # type: ignore[attr-defined]
                        active = sa_port.has_active_edition_for_offer(ctx.tenant_id, offer_id)
                        if not active:
                            has_unmet_waitlist = True
                            break
                    except Exception:  # noqa: BLE001
                        pass

                if has_unmet_waitlist:
                    suggestions.append(
                        Suggestion(
                            label="Tu lista de espera necesita una edición",
                            prompt=(
                                "Hay clientes en lista de espera sin edición programada. "
                                "Ayúdame a planificar la próxima cohorte."
                            ),
                            confidence=0.78,
                            category=SuggestionCategory.ACTION,
                            source_module="sales_agent",
                        )
                    )

            suggestions.sort(key=lambda s: s.confidence, reverse=True)
            return suggestions[:max_per_provider]
        finally:
            db.close()

    @staticmethod
    def _safe_int(fn: Callable[[], object], context: str = "") -> int:
        """Execute fn(); return 0 on exception."""
        try:
            value = fn() or 0
            return int(value)  # type: ignore[call-overload,no-any-return]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "sales_agent_provider_safe_int_failed",
                context=context,
                error=str(exc),
            )
            return 0

    @staticmethod
    def _safe_bool(fn: Callable[[], object], context: str = "") -> bool:
        """Execute fn(); return False on exception."""
        try:
            result = fn()
            return bool(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "sales_agent_provider_safe_bool_failed",
                context=context,
                error=str(exc),
            )
            return False

    @staticmethod
    def _safe_list(fn: Callable[[], object], context: str = "") -> list[object]:
        """Execute fn(); return [] on exception."""
        try:
            value = fn() or []
            return list(value)  # type: ignore[call-overload,no-any-return]
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "sales_agent_provider_safe_list_failed",
                context=context,
                error=str(exc),
            )
            return []

    @staticmethod
    def _is_older_than_24h(created_at_iso: str, now: datetime) -> bool:
        """Return True if the ISO timestamp is older than 24h from now."""
        try:
            if not created_at_iso:
                return False
            # Parse ISO string (may or may not have timezone)
            dt_str = created_at_iso.rstrip("Z")
            if "+" in dt_str:
                dt = datetime.fromisoformat(dt_str)
            else:
                dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (now - dt).total_seconds() > 86400
        except Exception:  # noqa: BLE001
            return True  # assume old if parse fails


__all__ = ["SalesAgentSuggestionProvider"]
