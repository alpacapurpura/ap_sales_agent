"""Campaign domain enums.

All enums use StrEnum for easy serialization to/from database strings.
"""

from __future__ import annotations

from enum import StrEnum


class CampaignType(StrEnum):
    """High-level campaign archetype. Drives orchestrator routing in S2."""

    AGENT_CONVERSATION = "agent_conversation"  # Sales Agent outbound 1:1 (S3 MVP 1)
    EMAIL_DRIP = "email_drip"  # MailerLite group → automation (PI-2)
    EMAIL_BROADCAST = "email_broadcast"  # One-shot email to segment (PI-2)
    EVENT_TRIGGER = "event_trigger"  # Multi-canal anclado a fecha (PI-3)
    PUSH_NOTIFICATION = "push_notification"  # OneSignal (PI-4)
    RETARGETING_EXPORT = "retargeting_export"  # CRM → Meta Ads audience (PI-3)


class CampaignStatus(StrEnum):
    """FSM states for Campaign lifecycle. See _FSM_TRANSITIONS in campaign.py."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"  # terminal
    CANCELED = "canceled"  # terminal


class StepType(StrEnum):
    """Polymorphic CampaignStep kinds. Each maps to a Pydantic step_config schema."""

    SEND_MESSAGE = "send_message"
    WAIT_DELAY = "wait_delay"
    BRANCH_ON_CONDITION = "branch_on_condition"
    CALL_SUBAGENT_BRIEF = "call_subagent_brief"  # invokes sales_agent OutboundOrchestrator (S3)
    MARK_COMPLETE = "mark_complete"


class TaskStatus(StrEnum):
    """CampaignTask lifecycle states."""

    PENDING = "pending"  # awaiting scheduler
    SCHEDULED = "scheduled"  # scheduled_at set, awaiting worker poll
    DISPATCHED = "dispatched"  # claimed by worker, in-flight
    SENT = "sent"  # message handed off to channel
    FAILED = "failed"  # exhausted retries / fatal error
    SKIPPED = "skipped"  # compliance/rate/budget gate refused
    BOUNCED = "bounced"  # channel returned hard bounce


class SegmentType(StrEnum):
    """Segment resolution mode."""

    DYNAMIC = "dynamic"  # filter resolved on-demand
    STATIC = "static"  # snapshot at create time


class SegmentFilterCombinator(StrEnum):
    """Top-level filter logic combinator."""

    ALL = "all"  # AND
    ANY = "any"  # OR
