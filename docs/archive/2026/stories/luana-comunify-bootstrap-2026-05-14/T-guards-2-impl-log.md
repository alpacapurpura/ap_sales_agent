# T-guards-2 — community_safety_no_nsfw (vision + text classifier)
<!-- voseo-allowed: cement chrome string "Subí otra" cited verbatim from 03-arch § 10.2 IMAGE_FALLBACK_RESPONSE (creator-economy voice profile supports voseo per S12 Slot 5 design) -->

**Ticket**: T-guards-2 — Guardrail community_safety_no_nsfw.
**R23**: AGENTIC production_code=true → Opus 4.7 EXCLUSIVE.
**Estimate vs actual**: 3h estimate / ~30min actual (batched).

## Skills Consulted

- **copilot-expert**: best-effort audit_log; tenant isolation; `_emit_audit_log` try/except.
- **sales-agent-expert**: anti-duplication §0 — grep verified zero `VisionClassifierProtocol` or `community_safety_no_nsfw` outside EP-13 placeholder. NEW surface.
- **tessl__graceful-degradation**: Rule 1 — `_CLASSIFIER_TIMEOUT_SEC = 5.0` on BOTH vision + text classifiers. Rule 2 — vision outage → skip attachment + continue text path (per-dependency error isolation: each attachment scored independently; text classifier consulted regardless of vision outcome).
- **tessl__pytest-api-testing**: `_FakeVisionClassifier` with `scores_by_url` map for per-URL programmable scores + `raise_on_call`; `_FakeLLMClassifier` for text path; 17 test cases.

## Step 0 GATE — Anti-duplication audit (2026-05-14)

```bash
grep -rln "VisionClassifierProtocol\|vision_classifier\|community_safety_no_nsfw"
```

Returns ONLY:
- EP-13 placeholder in extensions.py

No mirror. NEW guard. Both `_VisionClassifierLike` + `_LLMClassifierLike` Protocols are structural typing — concrete vision-AI impl deferred to Story 13+ (Anthropic vision multimodal OR AWS Rekognition / Azure Content Safety).

## Step 0.5 — Default flip detection

N/A.

## Files created

1. `agentic/guardrails/community_safety_no_nsfw.py` (~365 lines)
2. `tests/agentic_evals/guardrails/test_community_safety_no_nsfw.py` (~330 lines, 11 test cases)

## Implementation summary

- **Image path**: per-attachment loop via `_VisionClassifierLike.score(url, label='nsfw')` — first attachment with score > 0.85 → `block_pre_persist` + `IMAGE_FALLBACK_RESPONSE` (chrome Spanish neutro: "La imagen contiene contenido no permitido. Subí otra."). Other attachments NOT scored (cost guard short-circuit).
- **Text path**: post-image (or when no images), Haiku score classifier on `user_msg`. Score > 0.80 (text threshold lower than image 0.85 per 03-arch § 10.2) → `pending_moderation`.
- **Non-image attachments** (PDFs, docs) skip vision classifier (`is_image=False`).
- **Attachment value object**: frozen dataclass with `url`, `is_image`, `content_type`, `raw_bytes` (optional pre-fetched bytes).
- **`attachment_scores: dict`** — result surfaces all per-attachment scores (not just blocked) for observability.
- **Graceful degradation**: vision raise → `_consult_vision_classifier` returns None → skip attachment + continue. Text raise → pass-through. Audit_log raise → block still happens.

## Validators

- **V-AE-3** (5 NSFW image uploads — 4+/5 blocked): vision classifier paramterized via `_FakeVisionClassifier.scores_by_url` map; 3 dedicated image tests (single block + multiple-first-blocks-shortcircuits + non-image-skipped). End-to-end fire + audit asserted with severity=medium + `detection_source='image_vision'`.
- **V-AE-11** (audit_log + tenant isolation): 4 assertions including cross-tenant test (tenant_id propagation through audit row).

## Quality gates run

```
.venv/bin/pytest tests/agentic_evals/guardrails/test_community_safety_no_nsfw.py -v
11/11 PASS

.venv/bin/ruff check + format --check: clean.
```

## Deferred / gaps

- Real vision classifier impl (Anthropic multimodal): Story 13+.
- Real Haiku text classifier wiring: Story 13+.
- EP-13 extensions.py wiring: deferred.
- V-AE-11 chain ordering: cross-ticket (orchestrator integration).
