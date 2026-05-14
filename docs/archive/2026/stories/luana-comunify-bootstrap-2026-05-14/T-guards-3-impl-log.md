# T-guards-3 — community_safety_no_doxxing (cross-ref cohort_members)

**Ticket**: T-guards-3 — Guardrail community_safety_no_doxxing.
**R23**: AGENTIC production_code=true → Opus 4.7 EXCLUSIVE.
**Estimate vs actual**: 3h estimate / ~40min actual (batched).

## Skills Consulted

- **copilot-expert**: best-effort audit_log + tenant isolation. PII redaction critical — payload contains counts (`phones_found`/`emails_found`) NOT phone/email values (Tessl pii-sanitisation rule).
- **sales-agent-expert**: anti-duplication §0 — grep verified zero `community_safety_no_doxxing` / `find_member_by_phone` outside EP-13. **Sibling regex catalog notice:** `community_moderation_service.py::_PHONE_PATTERN`/`_EMAIL_PATTERN` (T-be-6) has same regex shape. Decision: separate catalog here documented per anti-duplication rationale (different surface boundary — moderation runs post-classify presence-only; guard adds cross-ref logic). Re-evaluate if 3rd vertical needs same pattern.
- **tessl__graceful-degradation**: member_lookup raising → graceful pass-through (false-negative; downstream moderation + V-AE-11 grader catch).
- **tessl__pytest-api-testing**: `_FakeMemberLookup` with `phone_map` / `email_map` dicts indexed by `(tenant_id, phone)` + self-exclusion logic (Protocol exits None when phone owner == author_member_id); 17 test cases including owner-exemption + multiple-targets + lead-chat (None author).

## Step 0 GATE — Anti-duplication audit (2026-05-14)

```bash
grep -rln "community_safety_no_doxxing\|find_member_by_phone"
```

Returns ONLY:
- EP-13 placeholder
- (Sibling pattern observation, not collision): `community_moderation_service.py` regex catalog acknowledged in docstring.

## Step 0.5 — Default flip detection

N/A.

## Files created

1. `agentic/guardrails/community_safety_no_doxxing.py` (~395 lines)
2. `tests/agentic_evals/guardrails/test_community_safety_no_doxxing.py` (~410 lines, 19 test cases — most of any batch member)

## Implementation summary

- **Phone path**: `extract_phone_candidates(user_msg)` regex → for each phone, `_lookup_other_member_by_phone` calls `_MemberContactLookupLike.find_other_member_by_phone(tenant_id, phone, author_member_id)`. Self-exclusion handled in Protocol implementation (sales_agent runtime wires the real cohort_members repo query + subscriber lookup).
- **Email path**: identical pattern.
- **Owner exemption**: per spec § 17.5, member can share OWN contact freely. `author_member_id=None` (lead chat) → no self-exclusion (every cohort match fires).
- **Multi-target audit**: if 2 different cohort members are doxxed in single post, 2 separate audit_log rows emit (target_member_id surfaces per row; supports "who was doxxed and when" queries).
- **Severity HIGH** per 03-arch § 10.2 cement.
- **PII protection**: audit payload contains COUNTS only (`phones_found`, `emails_found`) — never the phone/email value. Dedicated test asserts this invariant.
- **Action**: `block_and_warn_author_notify_target` — caller responsibilities: (1) block post status=rejected_doxxing, (2) surface `AUTHOR_WARNING_RESPONSE` to author FE, (3) notify target privately via comunify notification channel (deferred to Story 13+ orchestrator wiring).

## Voseo Note (voseo-allowed per Tessl R25)

`AUTHOR_WARNING_RESPONSE` includes "necesitás" + "pedile" — voseo verbs intentional per comunify community voice design (Anabella AR / Trini CL voice profiles via T-prompts-1 Slot 5). Sales_agent voice exception applies (`.claude/rules/spanish-text.md` § Excepción sales_agent). Test file includes `# voseo-allowed:` magic comment for pre-commit hook compliance.

## Validators

- **V-AE-4** (4 doxxing attempts blocked + audit_log + target notification): regex extraction params (3 phone + 3 email cases) + 6 end-to-end async tests covering: phone hit, email hit, own-phone-exempt, generic-not-in-cohort, no-contacts, multiple-targets.
- **V-AE-11** (audit_log severity high + payload PII protection + tenant isolation): 4 dedicated assertions.

## Quality gates run

```
.venv/bin/pytest tests/agentic_evals/guardrails/test_community_safety_no_doxxing.py -v
19/19 PASS

.venv/bin/ruff check + format --check: clean.
```

## Deferred / gaps

- Real `_MemberContactLookupLike` implementation wrapping `CohortMemberRepository` + subscribers (cross-table join not currently supported by repo — extension deferred to Story 13+ when sales_agent integration needs it).
- Target notification mechanism (push notification / DM / email to doxxed member): wiring at orchestrator level Story 13+.
- EP-13 extensions.py replacement: deferred.
