# T-17 — Implementation Log

**Ticket:** D-T2 cleanup — replace MessageModel stub in offer-studio conftest with real luana_core_copilot import
**Owner:** builder-agentic (Opus 4.7) — R23 mandatory
**Status:** **deferred to Story 7** (architect spec premise mismatched reality)
**Estimate:** 30min · **Actual:** ~15min (investigation + halt evaluation)

## Skills Consulted

- `copilot-expert` — confirmed luana-core-copilot infrastructure/models/ exports (no MessageModel)
- `sales-agent-expert` §3: MessageModel is sales_agent territory (NO touch); Story 7 lift
- `.claude/rules/hotfix-repro-mandatory.md` — R26 repro mandate: architect spec premise reproduced as FALSE pre-execution
- `.claude/rules/anti-duplication.md` — preserve single canonical MessageModel home (sales_agent)

## R26 — Reproduction of architect spec premise

Architect spec for T-17 (06-tickets.yaml + 03-arch.md §1 deviations + 05-guidelines.md §1.6):
> REPLACE the stub `class MessageModel(_Base)` block with real import:
> ```python
> from luana_core_copilot.infrastructure.models.message_model import MessageModel  # noqa: F401
> ```

**Reproduction check:**
```bash
find /home/chris/luana-platform/core/luana-core-copilot -name "message_model*"
# Output: (empty)

find /home/chris/AISALESHT/backend/src/modules/copilot -name "message_model*"
# Output: (empty)

find /home/chris/AISALESHT/backend/src/modules/sales_agent -name "message_model*"
# Output: /home/chris/AISALESHT/backend/src/modules/sales_agent/infrastructure/models/message_model.py
```

**Diagnosis:** Architect spec premise FALSE. `MessageModel` is `sales_agent` territory
(Story 7 lift), NOT `copilot` (Story 6). T-15-result.md confirms luana-core-copilot
package lift completed WITHOUT MessageModel (T-15 SHA 4c98bfe), because copilot module
never had a MessageModel — that's a sales_agent SQLA model that copilot's
`LeadModel.messages` FK relationship (declared in shared `luana_core_platform.infrastructure.models.crm`) targets.

The Story 5 stub exists precisely because **forward-importing sales_agent before Story 7
would violate DAG ordering** (luana_core_sales_agent doesn't exist until Story 7).

**Architect spec mismatch:** The directive "MessageModel now lifted to luana_core_copilot"
is incorrect — Story 6 lift does NOT include MessageModel.

## Step 0.5 — Default flip detection

NOT APPLICABLE — T-17 does not modify any config flag defaults.

## Halt criteria evaluation

Per 05-guidelines.md §6 (halt criteria):
- ✓ Trigger #3: "Registry contract change required — if AISALESHT has subtle inconsistency,
  surface to architect — D-T1 contract frozen requires arch ratification to bump."
- ✓ Trigger #5: "Scope expansion needed — any 'small refactor' touching files beyond §3
  list. Includes: introducing EP-1..EP-5 SDK abstraction, introducing BrandVoicePort
  (Story 7), new registries, new arch boundaries."

Lifting sales_agent.MessageModel into luana-core-copilot OR creating a fake
`luana_core_copilot.infrastructure.models.message_model` shim **would be Story 7
scope expansion** — violates `defer_notes` §5 in 06-tickets.yaml ("BrandVoicePort
introduction → Story 7. Story 5 deferred; Story 6 does NOT introduce. Story 7
architect handles consumer-side wiring.") — same principle applies to MessageModel
(sales_agent forward-coupling).

## Resolution

**Defer the entire T-17 modification to Story 7.** Story 7 sales_agent lift will:
1. Create `luana_core_sales_agent` package
2. Lift `sales_agent.infrastructure.models.message_model` → `luana_core_sales_agent.persistence.models.message_model`
3. AT THAT TIME, modify `core/luana-core-offer-studio/tests/conftest.py` lines 145-157 to:
   ```python
   from luana_core_sales_agent.persistence.models.message_model import MessageModel  # noqa: F401
   ```

This is parallel to the AppointmentModel stub handling (Story 8 territory per existing
spec §1.6 "AppointmentModel stub STAYS").

## Impact on Story 6 closure

- ✓ T-18 (next, integration smoke) — UNAFFECTED. offer-studio aggregate already
  GREEN (633 passed, 12 skipped per T-15 baseline). MessageModel + AppointmentModel
  stubs both stay; both serve their FK-target purpose.

- ✓ T-19, T-21 — UNAFFECTED. No interaction with conftest MessageModel stub.

- ⚠️ T-20 V-AG-4 arch fitness (`test_no_residual_test_stubs_post_story_6.py`) — needs
  spec adjustment. Per 03-arch.md §7.4: "Asserts `core/luana-core-offer-studio/tests/
  conftest.py` does NOT contain `class MessageModel(_Base)` declaration (must be import
  statement only)." This assertion needs to be relaxed to allow MessageModel stub
  pending Story 7. AppointmentModel allowlist already specified per spec — extend
  same pattern to MessageModel until Story 7.

  Per T-20 architect directive (spec §7.4): "AppointmentModel stub allowed per
  documented allowlist." MessageModel needs identical treatment.

  **Builder of T-20** (next ticket sequence) MUST author `test_no_residual_test_stubs_
  post_story_6.py` to allowlist BOTH MessageModel + AppointmentModel stubs as
  deferred to Stories 7 & 8 respectively. Test contract MUST cement: zero NEW
  stubs introduced post-Story-6 (only these two preserved stubs allowed).

## Files NOT modified

`core/luana-core-offer-studio/tests/conftest.py` — left UNTOUCHED. MessageModel stub
lines 145-157 stay verbatim. AppointmentModel stub lines 160-172 also stay verbatim
per existing 05-guidelines.md §1.6.

## Commit decision

**No commit for T-17.** Empty modification → no `git diff` to commit.

T-17 outcome: **deferred to Story 7**, documented here for audit trail. T-20 builder
will codify the deferral as arch fitness allowlist.

## Verdict

**deferred -> docs/product/stories/luana-copilot-engine/T-17-result.md** (Story 7 territory per R26 architect spec mismatch)
