"""DTOs for the Copilot chat endpoint and SSE event protocol."""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ── Request ──────────────────────────────────────────────────────────


class ClientContextDTO(BaseModel):
    """Data transfer object for client context.

    Focus mode was retired on 2026-04-21. Scoped edits are conveyed via
    ``selected_fields`` + the per-conversation mutation journal. The guided
    setup flag is derived server-side from the conversation's
    ``procedure_state["guided"]`` — the frontend does not send it.
    """

    current_route: str | None = None
    selected_fields: list[dict[str, str]] = Field(default_factory=list)
    form_data: dict[str, Any] = Field(default_factory=dict)
    locale: str = "es"


class CopilotChatRequest(BaseModel):
    """Request schema for copilot chat."""

    # `message` can be empty when the user sends only attachments (documents, audio, etc.).
    # The orchestrator enriches HumanMessage content with block-derived text, so an empty
    # `message` combined with non-empty `blocks` is a valid submission.
    message: str = Field("", max_length=4000)
    conversation_id: str | None = None
    blocks: list[dict[str, Any]] | None = None
    context: ClientContextDTO = Field(default_factory=ClientContextDTO)


# ── SSE Event Types ──────────────────────────────────────────────────
# [COPILOT-SSE-V2] → docs/domains/copilot/sse-protocol.md
# [COPILOT-SSE-V2-ONLY-F8] → docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
#
# F8 §5.4 — only the v2 block-streaming family is emitted. The legacy
# ``text_chunk`` channel was removed once the FE migrated to the
# block_delta render path. Unknown event types are still ignored
# gracefully by FEs that lag a deploy.

SSEEventType = Literal[
    # ── v2 streaming primitives ───────────────────────────────────────
    "message_start",  # marks start of new assistant message
    "block_start",  # new block begins (partial payload for text, full for others)
    "block_delta",  # streaming update for text blocks only
    "block_end",  # block finalized (full validated MessageBlock)
    "block_append",  # non-streaming block appended (tool results, citations, cards)
    "message_end",  # assistant message complete (final blocks list + tokens_used)
    # ── Tool + UI side channels ──────────────────────────────────────
    "tool_start",
    "tool_result",
    "ui_action",
    "proposal",
    "confirmation_required",
    # ── Lifecycle + observability ────────────────────────────────────
    "status",
    "tier_decision",  # CONTRACT §4.3 — emitted once, before first block_start
    "mutation_applied",  # CONTRACT §4.3 — emitted when a mutation is journaled
    "done",
    "error",
]


class SSEEvent(BaseModel):
    """Typed SSE event for the copilot stream."""

    event: SSEEventType
    data: dict[str, Any]

    def to_sse(self) -> str:
        """Format as SSE wire protocol."""
        import json

        return f"event: {self.event}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"


# ── Response (for non-streaming fallback) ────────────────────────────


class CopilotChatResponse(BaseModel):
    """Response schema for copilot chat."""

    conversation_id: str
    message: str


# ── Events ───────────────────────────────────────────────────────────


class RecordEventResponse(BaseModel):
    """Response schema for record event."""

    recorded: bool


class EventSummaryResponse(BaseModel):
    """Response schema for event summary."""

    events: list[Any]
    period_days: int
    tenant_id: str


class EventInsightsResponse(BaseModel):
    """Response schema for event insights."""

    friction_map: Any
    engagement: Any
    procedure_rates: Any
    period_days: int
    tenant_id: str


# ── Knowledge ────────────────────────────────────────────────────────


class IngestDocumentResponse(BaseModel):
    """Response schema for ingest document."""

    document_id: str
    chunks_indexed: int


class SearchResultItem(BaseModel):
    """Represent search result item data."""

    content: str
    score: float
    metadata: dict[str, Any]


class SearchKnowledgeResponse(BaseModel):
    """Response schema for search knowledge."""

    results: list[SearchResultItem]


# ── Nudge ────────────────────────────────────────────────────────────


class NudgeItem(BaseModel):
    """Represent nudge item data."""

    id: str
    type: str
    module_id: str
    title: str
    message: str
    suggested_prompt: str
    priority: int


class NudgeContextResponse(BaseModel):
    """Response schema for nudge context."""

    nudges: list[NudgeItem]


# ── Actions ──────────────────────────────────────────────────────────


class BrandExtractResponse(BaseModel):
    """Response DTO for the /brand/extract endpoint (visuals-only extraction)."""

    # Core colors
    primary_color: str | None = None
    secondary_color: str | None = None
    accent_color: str | None = None
    background_color: str | None = None
    surface_color: str | None = None
    text_primary_color: str | None = None
    text_secondary_color: str | None = None
    text_on_primary: str | None = None
    text_on_secondary: str | None = None
    # Extended colors
    color_palette: list[str] = Field(default_factory=list)
    neutral_colors: list[str] = Field(default_factory=list)
    semantic_colors: dict[str, Any] | None = None
    gradient_definitions: list[str] = Field(default_factory=list)
    color_usage_rules: str | None = None
    # Typography
    font_heading: str | None = None
    font_body: str | None = None
    font_accent: str | None = None
    font_weights: dict[str, Any] | None = None
    typography_scale: dict[str, Any] | None = None
    # Design system
    border_radius_style: str | None = None
    border_radius_values: dict[str, Any] | None = None
    shadow_style: str | None = None
    spacing_base: str | None = None
    visual_density: str | None = None
    # Visual personality
    brand_mood: dict[str, Any] | None = None
    visual_references: str | None = None
    photography_style: str | None = None
    icon_style: str | None = None
    # Style
    style_preset: str | None = None
    design_style: str | None = None
    usage_guidelines: list[str] = Field(default_factory=list)
    # Assets
    logo_url: str | None = None
    favicon_url: str | None = None
    images: list[str] = Field(default_factory=list)
    logos: dict[str, Any] | None = None
