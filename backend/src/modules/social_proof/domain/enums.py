"""Enums for the social_proof bounded context.

These are the public contract between the domain, the API, and the DB.
They MUST stay in sync with the VARCHAR values stored in Postgres — any
change here requires a new Alembic migration and an arch fitness test
update.
"""

from __future__ import annotations

from enum import StrEnum


class TestimonialMediaType(StrEnum):
    """Kind of media the testimonial content carries."""

    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"


class AuthorityType(StrEnum):
    """Classification for authority / credibility proof items."""

    CERTIFICATION = "certification"
    AWARD = "award"
    MEDIA_MENTION = "media_mention"
    PUBLISHED_WORK = "published_work"
    CLIENT_LOGO = "client_logo"
    CREDENTIAL = "credential"
    PARTNERSHIP = "partnership"
    SPEAKING = "speaking"
    PODCAST = "podcast"
    OTHER = "other"


class SourceTable(StrEnum):
    """Discriminator for the three social-proof source tables.

    Values MUST match the literal table names referenced by the
    ``social_proof_placements.source_table`` column.
    """

    TESTIMONIAL = "testimonial"
    AUTHORITY_ITEM = "authority_item"
    TEAM_MEMBER = "team_member"


class SurfaceType(StrEnum):
    """Where a social-proof item is shown.

    ``brand_homepage`` is tenant-wide (``surface_ref_id`` is NULL).
    The rest point at a concrete row via ``surface_ref_id``.
    """

    BRAND_HOMEPAGE = "brand_homepage"
    OFFER = "offer"
    LANDING_PAGE = "landing_page"
    EMAIL_SEQUENCE = "email_sequence"
    SALES_AGENT_KB = "sales_agent_kb"
