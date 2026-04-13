from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from src.modules.copilot.infrastructure.models.event_model import CopilotEventModel

logger = structlog.get_logger()


class CopilotEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        event_type: str,
        event_data: dict | None = None,
        conversation_id: UUID | None = None,
        route: str | None = None,
    ) -> CopilotEventModel:
        event = CopilotEventModel(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            event_data=event_data or {},
            conversation_id=conversation_id,
            route=route,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def _active_filter(self):
        return CopilotEventModel.deleted_at.is_(None)

    def get_user_behavior_summary(
        self,
        tenant_id: UUID,
        user_id: UUID,
        days: int = 30,
    ) -> dict[str, int]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(CopilotEventModel.event_type, func.count().label("cnt"))
            .where(
                CopilotEventModel.tenant_id == tenant_id,
                CopilotEventModel.user_id == user_id,
                CopilotEventModel.created_at >= cutoff,
                self._active_filter(),
            )
            .group_by(CopilotEventModel.event_type)
        )
        rows = self.db.execute(stmt).all()
        return {row.event_type: row.cnt for row in rows}

    def get_tenant_summary(self, tenant_id: UUID, days: int = 30) -> dict[str, int]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(CopilotEventModel.event_type, func.count().label("cnt"))
            .where(
                CopilotEventModel.tenant_id == tenant_id,
                CopilotEventModel.created_at >= cutoff,
                self._active_filter(),
            )
            .group_by(CopilotEventModel.event_type)
        )
        rows = self.db.execute(stmt).all()
        return {row.event_type: row.cnt for row in rows}

    def get_recent_events(
        self,
        tenant_id: UUID,
        limit: int = 100,
        event_type: str | None = None,
    ) -> list[CopilotEventModel]:
        stmt = (
            select(CopilotEventModel)
            .where(
                CopilotEventModel.tenant_id == tenant_id,
                self._active_filter(),
            )
            .order_by(CopilotEventModel.created_at.desc())
            .limit(limit)
        )
        if event_type:
            stmt = stmt.where(CopilotEventModel.event_type == event_type)
        return list(self.db.execute(stmt).scalars().all())

    def get_knowledge_search_stats(
        self,
        tenant_id: UUID,
        user_id: UUID,
        days: int = 30,
    ) -> dict:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = select(CopilotEventModel).where(
            CopilotEventModel.tenant_id == tenant_id,
            CopilotEventModel.user_id == user_id,
            CopilotEventModel.event_type == "knowledge_searched",
            CopilotEventModel.created_at >= cutoff,
            self._active_filter(),
        )
        events = list(self.db.execute(stmt).scalars().all())
        search_count = len(events)

        # Find most queried scope
        scope_counts: dict[str, int] = {}
        for ev in events:
            scope = (ev.event_data or {}).get("scope", "all")
            scope_counts[scope] = scope_counts.get(scope, 0) + 1

        most_queried_scope = max(scope_counts, key=scope_counts.get) if scope_counts else None
        return {"search_count": search_count, "most_queried_scope": most_queried_scope}

    def get_friction_map(self, tenant_id: UUID, days: int = 30) -> dict[str, int]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(CopilotEventModel.route, func.count().label("cnt"))
            .where(
                CopilotEventModel.tenant_id == tenant_id,
                CopilotEventModel.event_type == "copilot_opened",
                CopilotEventModel.created_at >= cutoff,
                CopilotEventModel.route.isnot(None),
                self._active_filter(),
            )
            .group_by(CopilotEventModel.route)
            .order_by(func.count().desc())
        )
        rows = self.db.execute(stmt).all()
        return {row.route: row.cnt for row in rows}

    def get_engagement_metrics(self, tenant_id: UUID, days: int = 30) -> dict:
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Total messages
        msg_count_stmt = (
            select(func.count())
            .select_from(CopilotEventModel)
            .where(
                CopilotEventModel.tenant_id == tenant_id,
                CopilotEventModel.event_type == "message_sent",
                CopilotEventModel.created_at >= cutoff,
                self._active_filter(),
            )
        )
        total_messages = self.db.execute(msg_count_stmt).scalar() or 0

        # Active users (unique user_ids on message_sent)
        active_stmt = select(
            func.count(func.distinct(CopilotEventModel.user_id)),
        ).where(
            CopilotEventModel.tenant_id == tenant_id,
            CopilotEventModel.event_type == "message_sent",
            CopilotEventModel.created_at >= cutoff,
            self._active_filter(),
        )
        active_users = self.db.execute(active_stmt).scalar() or 0

        messages_per_user_avg = round(total_messages / active_users, 1) if active_users else 0

        # Suggested vs typed
        suggested_stmt = (
            select(func.count())
            .select_from(CopilotEventModel)
            .where(
                CopilotEventModel.tenant_id == tenant_id,
                CopilotEventModel.event_type == "suggested_action_clicked",
                CopilotEventModel.created_at >= cutoff,
                self._active_filter(),
            )
        )
        suggested_count = self.db.execute(suggested_stmt).scalar() or 0

        return {
            "messages_per_user_avg": messages_per_user_avg,
            "active_users": active_users,
            "total_messages": total_messages,
            "suggested_vs_typed": {
                "suggested": suggested_count,
                "typed": max(0, total_messages - suggested_count),
            },
        }

    def get_procedure_completion_rates(self, tenant_id: UUID, days: int = 30) -> dict:
        cutoff = datetime.now(UTC) - timedelta(days=days)

        # Get procedure-related events
        stmt = select(CopilotEventModel).where(
            CopilotEventModel.tenant_id == tenant_id,
            CopilotEventModel.event_type.in_(["procedure_abandoned"]),
            CopilotEventModel.created_at >= cutoff,
            self._active_filter(),
        )
        events = list(self.db.execute(stmt).scalars().all())

        procedures: dict[str, dict] = {}
        for ev in events:
            data = ev.event_data or {}
            proc_id = data.get("procedure_id", "unknown")
            if proc_id not in procedures:
                procedures[proc_id] = {
                    "name": data.get("procedure_name", proc_id),
                    "started": 0,
                    "completed": 0,
                    "abandoned": 0,
                    "abandoned_steps": [],
                }
            if ev.event_type == "procedure_abandoned":
                procedures[proc_id]["abandoned"] += 1
                procedures[proc_id]["started"] += 1
                step = data.get("abandoned_at_step")
                if step is not None:
                    procedures[proc_id]["abandoned_steps"].append(step)

        # Calculate averages
        result = {}
        for proc_id, info in procedures.items():
            steps = info.pop("abandoned_steps")
            info["avg_abandoned_step"] = round(sum(steps) / len(steps), 1) if steps else None
            result[proc_id] = info

        return result

    # ── Cross-tenant methods (admin) ─────────────────────────────────────

    def get_global_summary(self, days: int = 30) -> dict[str, int]:
        """Event type counts without tenant filter."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(CopilotEventModel.event_type, func.count().label("cnt"))
            .where(
                CopilotEventModel.created_at >= cutoff,
                self._active_filter(),
            )
            .group_by(CopilotEventModel.event_type)
        )
        rows = self.db.execute(stmt).all()
        return {row.event_type: row.cnt for row in rows}

    def get_global_friction_map(self, days: int = 30) -> dict[str, int]:
        """copilot_opened by route, cross-tenant."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(CopilotEventModel.route, func.count().label("cnt"))
            .where(
                CopilotEventModel.event_type == "copilot_opened",
                CopilotEventModel.created_at >= cutoff,
                CopilotEventModel.route.isnot(None),
                self._active_filter(),
            )
            .group_by(CopilotEventModel.route)
            .order_by(func.count().desc())
        )
        rows = self.db.execute(stmt).all()
        return {row.route: row.cnt for row in rows}

    def get_global_engagement(self, days: int = 30) -> dict:
        """Cross-tenant engagement metrics."""
        cutoff = datetime.now(UTC) - timedelta(days=days)

        msg_count = (
            self.db.execute(
                select(func.count())
                .select_from(CopilotEventModel)
                .where(
                    CopilotEventModel.event_type == "message_sent",
                    CopilotEventModel.created_at >= cutoff,
                    self._active_filter(),
                ),
            ).scalar()
            or 0
        )

        active_users = (
            self.db.execute(
                select(func.count(func.distinct(CopilotEventModel.user_id))).where(
                    CopilotEventModel.event_type == "message_sent",
                    CopilotEventModel.created_at >= cutoff,
                    self._active_filter(),
                ),
            ).scalar()
            or 0
        )

        suggested_count = (
            self.db.execute(
                select(func.count())
                .select_from(CopilotEventModel)
                .where(
                    CopilotEventModel.event_type == "suggested_action_clicked",
                    CopilotEventModel.created_at >= cutoff,
                    self._active_filter(),
                ),
            ).scalar()
            or 0
        )

        return {
            "total_messages": msg_count,
            "active_users": active_users,
            "messages_per_user_avg": round(msg_count / active_users, 1) if active_users else 0,
            "suggested_vs_typed": {
                "suggested": suggested_count,
                "typed": max(0, msg_count - suggested_count),
            },
        }

    def get_global_procedure_rates(self, days: int = 30) -> dict:
        """Procedure completion rates cross-tenant."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = select(CopilotEventModel).where(
            CopilotEventModel.event_type.in_(
                ["procedure_abandoned", "procedure_completed"],
            ),
            CopilotEventModel.created_at >= cutoff,
            self._active_filter(),
        )
        events = list(self.db.execute(stmt).scalars().all())

        procedures: dict[str, dict] = {}
        for ev in events:
            data = ev.event_data or {}
            proc_id = data.get("procedure_id", "unknown")
            if proc_id not in procedures:
                procedures[proc_id] = {
                    "name": data.get("procedure_name", proc_id),
                    "started": 0,
                    "completed": 0,
                    "abandoned": 0,
                    "abandoned_steps": [],
                }
            if ev.event_type == "procedure_abandoned":
                procedures[proc_id]["abandoned"] += 1
                procedures[proc_id]["started"] += 1
                step = data.get("abandoned_at_step")
                if step is not None:
                    procedures[proc_id]["abandoned_steps"].append(step)
            elif ev.event_type == "procedure_completed":
                procedures[proc_id]["completed"] += 1
                procedures[proc_id]["started"] += 1

        result = {}
        for proc_id, info in procedures.items():
            steps = info.pop("abandoned_steps")
            info["avg_abandoned_step"] = round(sum(steps) / len(steps), 1) if steps else None
            result[proc_id] = info
        return result

    def get_events_grouped_by_tenant(self, days: int = 30) -> list[dict]:
        """Event counts per tenant for ranking."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(
                CopilotEventModel.tenant_id,
                func.count().label("event_count"),
            )
            .where(
                CopilotEventModel.created_at >= cutoff,
                self._active_filter(),
            )
            .group_by(CopilotEventModel.tenant_id)
            .order_by(func.count().desc())
        )
        rows = self.db.execute(stmt).all()
        return [{"tenant_id": row.tenant_id, "event_count": row.event_count} for row in rows]

    def get_recent_events_all(
        self,
        limit: int = 50,
        event_type: str | None = None,
    ) -> list[CopilotEventModel]:
        """Recent events without tenant filter (admin only)."""
        stmt = (
            select(CopilotEventModel)
            .where(self._active_filter())
            .order_by(CopilotEventModel.created_at.desc())
            .limit(limit)
        )
        if event_type:
            stmt = stmt.where(CopilotEventModel.event_type == event_type)
        return list(self.db.execute(stmt).scalars().all())

    def soft_delete_before(self, cutoff_date: datetime) -> int:
        stmt = (
            update(CopilotEventModel)
            .where(
                CopilotEventModel.created_at < cutoff_date,
                self._active_filter(),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        result = self.db.execute(stmt)
        return result.rowcount
