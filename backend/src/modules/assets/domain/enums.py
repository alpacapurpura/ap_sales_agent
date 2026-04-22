"""Enumeration types for the assets domain.

Assets are classified along three orthogonal axes:

* ``AssetType``    — physical kind (image/video/audio/document).
* ``AssetScope``   — lifecycle (ephemeral/library/deliverable).
* ``AssetPurpose`` — semantic intent (why this asset exists in the tenant).

Scope drives retention + visibility in search. Purpose drives how the asset
is consumed by downstream modules (sales_agent, landing, etc.).
"""

from enum import StrEnum


class AssetType(StrEnum):
    """Physical kind of asset."""

    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


class StorageProvider(StrEnum):
    """Backend that holds the binary payload."""

    LOCAL = "LOCAL"
    S3 = "S3"
    R2 = "R2"


class AssetStatus(StrEnum):
    """Legacy processing status for AI image analysis pipeline."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AssetScope(StrEnum):
    """Lifecycle classification.

    - ``ephemeral``: chat-scoped upload for info extraction. TTL applies.
      Excluded from cross-tenant asset search.
    - ``library``: official tenant asset, no expiry, discoverable in search.
    - ``deliverable``: subset of library that is linked to a domain entity
      (offer/flow) with a role — these can be auto-attached by agents.
    """

    EPHEMERAL = "ephemeral"
    LIBRARY = "library"
    DELIVERABLE = "deliverable"


class AssetPurpose(StrEnum):
    """Semantic intent of the asset — closed taxonomy.

    Adding a new value requires a migration + architecture review.
    Consumers (tools, services) key off this to decide how to surface
    the asset (e.g. ``sales_agent`` only forwards ``offer_collateral`` /
    ``legal_doc``).
    """

    CONTEXT_EXTRACT = "context_extract"
    VISUAL_REFERENCE = "visual_reference"
    BRAND_ASSET = "brand_asset"
    OFFER_COLLATERAL = "offer_collateral"
    LEGAL_DOC = "legal_doc"
    TESTIMONIAL = "testimonial"
    KNOWLEDGE_SOURCE = "knowledge_source"


class ExtractionStatus(StrEnum):
    """State of text-extraction for document/audio assets.

    Independent from ``AssetStatus`` (which tracks the AI image pipeline)
    so both workflows can progress without collisions.
    """

    PENDING = "pending"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    SKIPPED = "skipped"  # asset type that has no extractable text (image/video)
    FAILED = "failed"


# Default scope/purpose for each upload source — keeps call-sites terse.
DEFAULT_SCOPE_FOR_PURPOSE: dict[AssetPurpose, AssetScope] = {
    AssetPurpose.CONTEXT_EXTRACT: AssetScope.EPHEMERAL,
    AssetPurpose.VISUAL_REFERENCE: AssetScope.EPHEMERAL,
    AssetPurpose.BRAND_ASSET: AssetScope.LIBRARY,
    AssetPurpose.OFFER_COLLATERAL: AssetScope.DELIVERABLE,
    AssetPurpose.LEGAL_DOC: AssetScope.DELIVERABLE,
    AssetPurpose.TESTIMONIAL: AssetScope.LIBRARY,
    AssetPurpose.KNOWLEDGE_SOURCE: AssetScope.LIBRARY,
}
