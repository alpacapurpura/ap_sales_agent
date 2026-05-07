# 07-merge.md — maintenance-skill-sales-agent-audit

> Owner: `/pm`
> Date: 2026-05-06T20:25:00Z
> Verdict source: `T-1-review.md` (APPROVED) + `CHECKPOINTS.md` (C1-C5 sealed APPROVED)
> Story type: maintenance / doc-engineering (single ticket, production_code=false R23)

## Precondiciones verificadas

- [x] Auditor APPROVED (`T-1-review.md`: 0 FAIL · 3 WARN non-blocking · 4 PASS · 11 N/A)
- [x] CHECKPOINTS.md C1-C5 grid sealed APPROVED
- [x] gate-output.json any_fail=false (ruff lint+format+pytest 10/10 PASS)
- [x] Hard gates: A7 zero_src_changes, 11/11 must_pass validators GREEN
- [x] Anti-duplication inventory sincronizado (.claude/rules/anti-duplication.md)
- [x] Commits pushed: 376ebbc6 (build) + 6fd638a6 (housekeeping) + 0770988a (auditor)

## Capability promotion — NA

Story es maintenance/doc-engineering — NO toca runtime, NO promueve capability nueva. Skill `sales-agent-expert` es SSoT documental, no producto user-facing. NO update a `docs/product/capabilities/sales_agent/*.yaml`.

## modules/{m}.md auto-list — NA

Skill cambió, módulo `sales_agent` narrativa NO cambió. NO refresh marker auto-list.

## learnings.md — NA

Audit rutinario sin learnings cardinales nuevos. Verdict APPROVED first-pass sin escalations o re-builds. Workflow `/dev-team` Conv 2 + `/auditor` Conv 3 ejecutó nominal.

## Steps ejecutados

1. ✅ Precondiciones verificadas (above)
2. ✅ `07-merge.md` escrito (este archivo)
3. ⏭️ Capability promotion: SKIP (NA — explained above)
4. ⏭️ `reconcile_capabilities.py`: SKIP (NA — no capability changes)
5. ⏭️ `modules/sales_agent.md` auto-list: SKIP (NA)
6. ⏳ `python3 scripts/generate_backlog.py` — refresh BACKLOG.{yaml,md} (auto via pre-commit hook Section 6)
7. ⏳ Archive `docs/product/stories/maintenance-skill-sales-agent-audit/` → `docs/archive/2026/stories/maintenance-skill-sales-agent-audit/`
8. ⏭️ learnings.md: SKIP (NA)
9. ⏳ Update `docs/product/outcomes/pi-12-sales-agent-eval-foundation.md`: mark story done en story_ids list + tabla "Done"

## Final state transition

- Story: `state: reviewing → done`
- Folder: `docs/product/stories/maintenance-skill-sales-agent-audit/` → archive immutable

## Stories desbloqueadas conceptualmente

Skill `sales-agent-expert` ahora es SSoT auditado. Stories downstream que dependen del skill auditado:

1. `eval-foundation-tenant-seed-data` (state=ready, ya puede arrancar Conv 2)
2. `eval-foundation-simulator-homologation` (state=refining)
3. `sales-agent-personas-instrumented-runtime` (state=refining)
4. `sales-agent-goldens-3-tenants-dataset` (state=refining)
5. `sales-agent-voice-fidelity-grader-runtime` (state=refining)
6. `sales-agent-eval-pass-k-tracking` (state=refining)
7. `sales-agent-voice-fidelity-ci-gate` (state=refining)
8. `sales-agent-eval-cost-budget-cap` (state=refining)
9. `sales-agent-adversarial-jailbreak-suite` (state=refining)

## Commit & push

Merge commit incluye:
- Archive move (git mv folder)
- Outcome update (story_ids: maintenance-skill-sales-agent-audit → done section)
- BACKLOG.{yaml,md} regen (auto via hook)
- Este 07-merge.md (committed pre-archive en story folder original ANTES del git mv)
