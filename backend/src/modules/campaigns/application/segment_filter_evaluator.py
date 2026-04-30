"""SegmentFilterEvaluator — compiles PredefinedSegmentFilter to SQLA WHERE predicate.

SSoT for segment-filter semantics. SQL-side (production-grade 1000 clientes)
+ in-memory (testing).

NEVER loads leads in Python. NEVER constructs SQL strings (uses SQLA expressions only).

Architecture note:
- Fields on LeadModel (fit_score, intent_score, temperature, country, is_blacklisted,
  last_interaction_date, telegram_id, whatsapp_id, instagram_id, tiktok_id, created_at)
  — direct LeadModel column predicates.
- Fields on CustomerProfileModel (lifecycle_stage, lead_source) — correlated EXISTS
  subquery via LeadModel.customer_id FK (JOIN customer_profiles).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from sqlalchemy import Boolean, ColumnElement, and_, exists, false, or_, select

from src.modules.campaigns.domain.enums import SegmentFilterCombinator
from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter
from src.shared.infrastructure.models.crm import CustomerProfileModel, LeadModel

if TYPE_CHECKING:
    import datetime as dt

logger = structlog.get_logger(__name__)


class _ChannelColumnMissingError(ValueError):
    """Raised when a ChannelIdentifier has no direct column on LeadModel."""


def _build_lifecycle_clause(lifecycle_stage: list[str]) -> ColumnElement[Boolean]:
    """EXISTS subquery for lifecycle_stage (lives on CustomerProfileModel)."""
    subq = (
        select(CustomerProfileModel.id)
        .where(
            CustomerProfileModel.id == LeadModel.customer_id,
            CustomerProfileModel.lifecycle_stage.in_(lifecycle_stage),
        )
        .correlate(LeadModel)
    )
    return exists(subq)


def _build_source_clause(source: list[str]) -> ColumnElement[Boolean]:
    """EXISTS subquery for lead_source (lives on CustomerProfileModel)."""
    subq = (
        select(CustomerProfileModel.id)
        .where(
            CustomerProfileModel.id == LeadModel.customer_id,
            CustomerProfileModel.lead_source.in_(source),
        )
        .correlate(LeadModel)
    )
    return exists(subq)


def _build_channel_clause(has_channel_id: list[str]) -> ColumnElement[Boolean]:
    """Builds IS NOT NULL clauses for channel id columns."""
    channel_clauses: list[ColumnElement[Boolean]] = []
    for ch in has_channel_id:
        col = getattr(LeadModel, ch, None)
        if col is None:
            msg = f"channel column {ch} no existe en LeadModel"
            raise _ChannelColumnMissingError(msg)
        channel_clauses.append(col.is_not(None))
    if len(channel_clauses) == 1:
        return channel_clauses[0]
    return or_(*channel_clauses)


class SegmentFilterEvaluator:
    """Pure-function compiler: PredefinedSegmentFilter → SQLA ColumnElement.

    NEVER loads leads in Python. NEVER constructs SQL strings.
    Caller wraps result with: AND(LeadModel.tenant_id == tenant_id, returned_predicate)
    """

    def _collect_sql_clauses(
        self,
        filter_dsl: PredefinedSegmentFilter,
    ) -> list[ColumnElement[Boolean]]:
        """Collect all non-None filter clauses as SQLA expressions."""
        clauses: list[ColumnElement[Boolean]] = []

        if filter_dsl.lifecycle_stage:
            clauses.append(_build_lifecycle_clause(filter_dsl.lifecycle_stage))

        if filter_dsl.source:
            clauses.append(_build_source_clause(filter_dsl.source))

        if filter_dsl.temperature:
            clauses.append(LeadModel.temperature.in_(filter_dsl.temperature))

        if filter_dsl.score_range:
            sr = filter_dsl.score_range
            if sr.fit_score_min is not None:
                clauses.append(LeadModel.fit_score >= sr.fit_score_min)
            if sr.fit_score_max is not None:
                clauses.append(LeadModel.fit_score <= sr.fit_score_max)
            if sr.intent_score_min is not None:
                clauses.append(LeadModel.intent_score >= sr.intent_score_min)
            if sr.intent_score_max is not None:
                clauses.append(LeadModel.intent_score <= sr.intent_score_max)

        if filter_dsl.country:
            normalized = [c.lower() for c in filter_dsl.country]
            clauses.append(LeadModel.country.in_(normalized))

        if filter_dsl.created_at_range:
            cr = filter_dsl.created_at_range
            if cr.gte is not None:
                clauses.append(LeadModel.created_at >= cr.gte)
            if cr.lte is not None:
                clauses.append(LeadModel.created_at <= cr.lte)

        if filter_dsl.last_interaction_at_range:
            lr = filter_dsl.last_interaction_at_range
            if lr.gte is not None:
                clauses.append(LeadModel.last_interaction_date >= lr.gte)
            if lr.lte is not None:
                clauses.append(LeadModel.last_interaction_date <= lr.lte)

        if filter_dsl.tags and filter_dsl.tags.tags:
            tf = filter_dsl.tags
            if tf.mode == "any":
                clauses.append(LeadModel.profile_data["tags"].op("?|")(tf.tags))
            else:
                clauses.append(LeadModel.profile_data["tags"].op("?&")(tf.tags))

        if filter_dsl.is_blacklisted is not None:
            clauses.append(LeadModel.is_blacklisted == filter_dsl.is_blacklisted)

        if filter_dsl.has_channel_id:
            clauses.append(_build_channel_clause(filter_dsl.has_channel_id))

        return clauses

    def to_sql_predicate(
        self,
        filter_dsl: PredefinedSegmentFilter,
        *,
        tenant_id: UUID,
        at: dt.datetime | None = None,
    ) -> ColumnElement[Boolean]:
        """Compose SQL WHERE predicate for LeadModel queries.

        Combinator semantics:
        - filter_dsl.combinator == ALL → AND across all non-None fields
        - filter_dsl.combinator == ANY → OR across all non-None fields

        Args:
            filter_dsl: Validated PredefinedSegmentFilter DSL.
            tenant_id: Tenant UUID — used for logging only; caller adds tenant filter.
            at: Optional point-in-time (reserved for future temporal filters).

        Returns:
            SQLA ColumnElement[Boolean] representing the filter predicate.
        """
        clauses = self._collect_sql_clauses(filter_dsl)

        if not clauses:
            logger.warning(
                "segment_filter_empty_predicate",
                tenant_id=str(tenant_id),
                hint="All filter fields are None — returns false() to avoid full-table scan",
            )
            return false()

        if filter_dsl.combinator == SegmentFilterCombinator.ANY:
            return or_(*clauses)
        return and_(*clauses)

    def _collect_eval_results(
        self,
        filter_dsl: PredefinedSegmentFilter,
        lead: dict[str, Any],
    ) -> list[bool]:
        """Collect per-field boolean results for in-memory evaluation."""
        results: list[bool] = []

        if filter_dsl.lifecycle_stage:
            results.append(lead.get("lifecycle_stage") in filter_dsl.lifecycle_stage)

        if filter_dsl.source:
            results.append(lead.get("lead_source") in filter_dsl.source)

        if filter_dsl.temperature:
            results.append(lead.get("temperature") in filter_dsl.temperature)

        if filter_dsl.score_range:
            sr = filter_dsl.score_range
            fit = int(lead.get("fit_score") or 0)
            intent = int(lead.get("intent_score") or 0)
            if sr.fit_score_min is not None:
                results.append(fit >= sr.fit_score_min)
            if sr.fit_score_max is not None:
                results.append(fit <= sr.fit_score_max)
            if sr.intent_score_min is not None:
                results.append(intent >= sr.intent_score_min)
            if sr.intent_score_max is not None:
                results.append(intent <= sr.intent_score_max)

        if filter_dsl.country:
            lead_country = (lead.get("country") or "").lower()
            results.append(lead_country in [c.lower() for c in filter_dsl.country])

        if filter_dsl.created_at_range:
            cr = filter_dsl.created_at_range
            created = lead.get("created_at")
            if created is not None:
                if cr.gte is not None:
                    results.append(created >= cr.gte)
                if cr.lte is not None:
                    results.append(created <= cr.lte)

        if filter_dsl.last_interaction_at_range:
            lr = filter_dsl.last_interaction_at_range
            last_int = lead.get("last_interaction_date")
            if last_int is not None:
                if lr.gte is not None:
                    results.append(last_int >= lr.gte)
                if lr.lte is not None:
                    results.append(last_int <= lr.lte)

        if filter_dsl.tags and filter_dsl.tags.tags:
            tf = filter_dsl.tags
            profile_data = lead.get("profile_data") or {}
            lead_tags: list[str] = profile_data.get("tags") or []
            if tf.mode == "any":
                results.append(any(t in lead_tags for t in tf.tags))
            else:
                results.append(all(t in lead_tags for t in tf.tags))

        if filter_dsl.is_blacklisted is not None:
            results.append(bool(lead.get("is_blacklisted", False)) == filter_dsl.is_blacklisted)

        if filter_dsl.has_channel_id:
            channel_results = [lead.get(ch) is not None for ch in filter_dsl.has_channel_id]
            results.append(any(channel_results))

        return results

    def evaluate_one(
        self,
        filter_dsl: PredefinedSegmentFilter,
        lead: dict[str, Any],
    ) -> bool:
        """In-memory eval (tests + edge cases). lead is dict-like snapshot.

        Keys expected:
            lifecycle_stage, temperature, fit_score, intent_score,
            lead_source, country, created_at, last_interaction_date,
            profile_data (dict with optional "tags" key), is_blacklisted,
            telegram_id, whatsapp_id, instagram_id, tiktok_id
        """
        results = self._collect_eval_results(filter_dsl, lead)

        if not results:
            return False  # empty filter → no match (mirrors false())

        if filter_dsl.combinator == SegmentFilterCombinator.ANY:
            return any(results)
        return all(results)
