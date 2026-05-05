# Process Improvements Investigation 2026-05-05

> **Origen:** session 2026-05-05 implementing R1-R9 + A0 (context-builder hardening). Chris ratificó investigación adicional 4 áreas (de 10 sugeridas en `process-improvement-handoff-2026-05-05.md`).
> **Owner próxima sesión:** PM ratifica R12-R20 — decide cuáles implementar PI-13.
> **Goal:** producir R12+ recomendaciones priorizadas para evolución continua del proceso SDD nivel 3.

---

## Índice

1. [Área #1 — Métricas observables del pipeline](#área-1--métricas-observables-del-pipeline)
2. [Área #4 — Skill consolidation audit](#área-4--skill-consolidation-audit)
3. [Área #5 — Memoria de patterns aprendidos](#área-5--memoria-de-patterns-aprendidos)
4. [Área #6 — Auditor self-improvement](#área-6--auditor-self-improvement)
5. [R12-R20 priorizadas](#r12-r20-priorizadas)
6. [Sinergias entre áreas](#sinergias-entre-áreas)

---

## Área #1 — Métricas observables del pipeline

### Problema actual

Pipeline `/po → /architect → /dev-team → /auditor` opera ciego:
- No medimos tokens consumidos por phase/ticket → extrapolación lineal post-hoc (3.3M / 5 tickets = 660k/ticket — pero realidad varía 5x según complexity)
- No medimos defect rate (auditor verdict APPROVED vs CHANGES_REQUESTED vs ESCALATED ratio)
- No medimos rework rate (cuántos tickets vuelven a `tests-failing` post-pushed)
- No medimos time-to-merge (story start → merge wall-clock)
- No medimos auditor catch rate (cuántos bugs llegaron a S2+ pese a APPROVED)

Sin métricas no podemos validar que R1-R9 realmente bajan tokens / mejoran calidad. Sin baseline no hay mejora medible.

### Propuesta R12 — `process_run_metrics` infraestructura

**Layer 1 — Capture mecánico (cheap):**

Cada agent run escribe linea JSONL a `docs/process/metrics/runs.jsonl` (gitignored, append-only):

```json
{
  "ts": "2026-05-05T14:30:00Z",
  "pi": "PI-12",
  "sprint": "S1-eval-runner",
  "story": "sales-agent-litellm-canonicalization",
  "ticket": "T-1",
  "agent": "builder-backend",
  "model": "sonnet",
  "phase": "implement",
  "iter": 1,
  "tokens_in": 245000,
  "tokens_out": 18500,
  "cache_read": 89000,
  "cache_write": 12000,
  "tool_calls": 67,
  "duration_ms": 423000,
  "verdict": "tests_passing",
  "files_modified": 12,
  "loc_delta": "+342/-156"
}
```

**Mecanismo de captura:**
- Opción A: hook en agent prompt (cada agent termina con append JSONL)
- Opción B: parse Claude Code session transcripts post-run (orchestrator like `/dev-team` lee result + extracts metrics)
- Opción C: Anthropic SDK telemetry middleware (si usaramos SDK direct vía claude-api skill)

**Recomendado:** Opción B (orchestrator parses) — zero invasive a agent prompts, retroactive sobre transcripts existentes.

**Layer 2 — Aggregation & visualization:**

Python script `scripts/process_metrics_report.py` lee `runs.jsonl` y produce:
- Tokens per ticket (avg, p50, p95, max) por surface (BE/FE/AGENTIC)
- Tokens per agent type (architect vs builder vs auditor vs context-builder)
- Cost per PI ($USD calculated from model pricing snapshot)
- Defect rate per surface (% APPROVED first-pass vs CHANGES_REQUESTED)
- Rework rate (% tickets re-pushed post-test-failing)
- Time-to-merge histogram

Output: markdown report en `docs/process/metrics/report-{date}.md` + maybe Streamlit panel `/admin/process-metrics`.

**Layer 3 — A/B comparison (Área #2 from handoff sugerida):**

Spawn 2 builders parallel para mismo ticket (con + sin context-builder), capture both runs, compare metrics. Validate R1+R2 ROI claim (-30-40% tokens).

**Esfuerzo:** 4-6h Layer 1+2. Layer 3 6-8h adicional.

**Beneficio:** evidence-driven mejoras futuras. Catch regressions process (cuando una nueva regla agrega 50k tokens silenciosa).

### Propuesta R13 — Cost tracking del proceso mismo (Área #9 handoff)

Tabla `pi_phase_token_usage` extension natural de R12:

```sql
CREATE TABLE pi_phase_token_usage (
  pi_id TEXT,
  sprint_id TEXT,
  story_id TEXT,
  phase TEXT,           -- po | architect | dev-team | auditor
  agent TEXT,
  model TEXT,
  tokens_in_sum BIGINT,
  tokens_out_sum BIGINT,
  cache_read_sum BIGINT,
  cost_usd NUMERIC(10,4),
  duration_ms_sum BIGINT,
  PRIMARY KEY (pi_id, sprint_id, story_id, phase, agent)
);
```

Si Postgres dev local: simple migration + worker que reads `runs.jsonl` y agrega.

Permite queries:
- "PI-12 cost total"
- "Sprint S1 tokens by phase"
- "Builder-backend avg tokens per ticket trending"
- "% tokens spent on context-builder (Haiku) vs Opus reasoning"

**Esfuerzo:** 2h migration + worker. Asume R12 done.

---

## Área #4 — Skill consolidation audit

### Problema actual

Listing skills en sistema:
- 50+ skills definidos en `.claude/skills/`
- ¿Cuáles realmente se invocan en práctica? Sin telemetría no sabemos.
- Skills redundantes: `nicolify-feature` vs `pm` overlap parcial (ambos orchestate fases)
- Skills obsoletos: `tessl__chakra-ui` (no usamos Chakra), `tessl__tanstack-start` (no usamos TanStack)
- Skills duplicados: `architect-be` + `architect-fe` + `architect-agentic` + orchestrator `architect` — cuál carga PM real?

Cognitive load: agent prompt template MENTIONS skills disponibles; cada extra skill = ~50-200 tokens prompt overhead × N agents × M sessions = waste.

### Propuesta R14 — Skill usage audit pasivo + decommission proposal

**Step 1 — Audit (1h script):**

Script `scripts/audit_skill_usage.py`:
1. Walk `.claude/skills/*/SKILL.md`
2. For each skill name, grep:
   - `git log --all --oneline -- ".claude/skills/{name}/"` (cuándo modificado last)
   - `grep -rln "Skill tool.*{name}\|invoke.*{name}\|/${name}" docs/` (refs en process docs)
   - `grep -rln "{name}" docs/projects/active/ docs/pm-nico/` (refs en active work)
3. Output table:

| Skill | Last commit | Refs in docs | Refs in active PIs | Status |
|---|---|---|---|---|
| `pm` | 2026-05-05 | 47 | 12 | ACTIVE |
| `tessl__chakra-ui` | 2026-04-01 | 0 | 0 | DECOMMISSION CANDIDATE |
| `architect` | 2026-05-04 | 5 | 3 | ACTIVE |
| `nicolify-feature` | 2026-04-15 | 2 | 0 | LEGACY — superseded by /pm orchestration |
| ... | ... | ... | ... | ... |

**Step 2 — Decommission proposal:**

Per skill marked DECOMMISSION CANDIDATE / LEGACY:
- Move to `.claude/skills/_archive/` (gitignored from search but kept para reference)
- Update agent prompts to remove skill from `skills:` frontmatter
- Update CLAUDE.md skill routing tables
- Document in `docs/process/skill-decommission-log.md` why removed

**Step 3 — Skill consolidation:**

Per overlap detected (e.g., `nicolify-feature` ⊂ `pm`):
- Merge into canonical skill
- Add migration note in deprecated skill: "moved to {canonical}"

**Esfuerzo:** 2h audit + 4h decommission/consolidation execution. Cap 10 skills per pass para review-friendly.

**Beneficio:** -10-20% prompt overhead avg agent. Más importante: cognitive clarity para Chris + agents (un skill canonical per concern).

**Riesgos:** decommission breaks something silently used. Mitigation: 30-day deprecation window — skill marked deprecated en frontmatter, agents warn pero no fail. Después archive si zero usage.

### Propuesta R15 — Skill SSoT registry

Single file `docs/process/skill-registry.md` (auto-generated from `.claude/skills/*/SKILL.md` frontmatter):

| Skill | Owner | Phase | Triggers | Status | Last review |
|---|---|---|---|---|---|

Updated by R14 audit script. Replaces ad-hoc skill mention en CLAUDE.md y AGENTS.md.

**Esfuerzo:** 1h script + integración con R14.

---

## Área #5 — Memoria de patterns aprendidos

### Problema actual

Patterns recurrentes emergen durante implementation pero NO persisten:
- "Fixture lazy import to keep collection cheap" (PI-12 Story B T-2 — 3 usos)
- "Mock LiteLLM provider via factory not direct import" (PI-12 Story A T-7)
- "Subclass BaseObservabilityContext, never mirror" (anti-duplication.md catches but pattern positive)
- "Use `magic_factory()` from `model_factory_boy` for test data setup"
- "Idempotent migration template: raw SQL IF NOT EXISTS + enum reference, not sa.Enum()"

Cada vez que un nuevo dev (qwen, sonnet, opus) toma ticket: re-aprende pattern desde scratch o repeatedly busca grep cross-codebase.

### Propuesta R16 — `pattern-memory` skill + repository

**Skill nueva `pattern-memory`:**

```yaml
---
name: pattern-memory
description: Returns curated reusable code patterns for Nicolify implementations. Use when builder asks "how to do X" / "show me pattern for Y" / "is there an existing helper for Z". Patterns vivent en docs/process/patterns/*.md. Each pattern: when to use, code snippet, anti-pattern, references.
---
```

**Repository structure:**

```
docs/process/patterns/
├── INDEX.md                              # Browseable list por category
├── testing/
│   ├── lazy-import-fixture.md
│   ├── factory-boy-tenant-data.md
│   ├── mock-litellm-provider.md
│   └── ...
├── domain/
│   ├── extend-shared-callback-handler.md
│   ├── domain-event-cross-module.md
│   └── ...
├── infrastructure/
│   ├── idempotent-migration.md
│   ├── async-circuit-breaker.md
│   └── ...
├── api/
│   ├── pydantic-v2-response-model.md
│   ├── tenant-header-injection.md
│   └── ...
├── frontend/
│   ├── shadcn-form-rhf-zod.md
│   ├── react-query-suspense.md
│   └── ...
└── agentic/
    ├── prompt-cache-slot-arch.md
    ├── deepagents-subagent-isolation.md
    └── ...
```

**Pattern format:**

```markdown
# Pattern: Lazy import fixture (test collection cheap)

## When to use
- Heavy test fixture imports something that triggers DB connect / Qdrant init / LLM client init
- Pytest collection time grows unbounded as tests added
- CI unit phase taking >2min

## Code
```python
# tests/conftest.py
import pytest

@pytest.fixture
def heavy_service():
    # Import inside fixture, NOT at module top
    from src.modules.heavy.application.service import HeavyService
    return HeavyService()
```

## Anti-pattern
```python
# Top-level import → triggers init at collection time
from src.modules.heavy.application.service import HeavyService

@pytest.fixture
def heavy_service():
    return HeavyService()
```

## Why
Pytest collects ALL test modules upfront. Top-level imports execute regardless of which tests run. Lazy import inside fixture defers cost to actual test execution.

## References
- PI-12 S1 Story B T-2 commit 6abfef7b — applied to langdetect fixture
- pytest docs: https://docs.pytest.org/en/stable/explanation/fixtures.html#a-note-about-fixture-cleanup
```

**Skill workflow:**

User asks builder: "how do I avoid pytest collection slowdown?" → builder invokes `pattern-memory` skill → skill greps `docs/process/patterns/` for keywords → returns matching patterns + INDEX section anchors.

**Pattern lifecycle:**

- Capture: cuando dev/auditor encuentra pattern reusable → add to repository (manual o via /pm escalation when 2+ tickets used same)
- Promote: pattern usado >5 veces → considera lift to canonical helper (shared lib, reusable fixture, code template)
- Deprecate: pattern obsolescido por library upgrade → mark DEPRECATED + link to replacement

**Esfuerzo:** 2h skill creation + INDEX.md scaffolding. 8-12h sembrar inicial 20-30 patterns desde git log mining (commits con "pattern:" prefix or auditor recommendations). Ongoing: ~30min per pattern added.

**Beneficio:** quality consistency cross-tickets. Onboarding dev faster (pattern library = institutional memory). Anti-duplication preventivo (pattern-memory shows "ya hay helper X").

### Propuesta R17 — Auto-pattern extraction

Script `scripts/extract_patterns_from_diffs.py`:
- Walk last 30 days commits
- Identify diffs que touched 2+ files in same way (similar regex addition, similar test setup, similar fixture)
- Generate pattern candidate stub en `docs/process/patterns/_candidates/`
- PM review + promotes to canonical patterns/ if reusable

Heuristics:
- Same 5+ lines added in 3+ files cross-module → candidate
- New helper function added with TODO comment "lift to shared if reused" → candidate

**Esfuerzo:** 6-8h script. Captures patterns that would otherwise be ad-hoc reimplemented.

---

## Área #6 — Auditor self-improvement

### Problema actual

Auditor APPROVED bug crítico D4 (PI-12 S1 T-1) pese a:
- 13 categorías checklist
- 78 arch fitness gates
- /test-backend full suite

Bug llegó a S1 → T-1-bis micro-ticket nuevo. R3 (downstream regression scope rule) addresses esto al requerir auditor run downstream tests cross-surface.

Pero R3 solo cubre downstream pre-defined en tabla SSoT. ¿Qué de bugs en surfaces NO cubiertas en tabla? Auditor no introspecta pattern bugs.

### Propuesta R18 — Auditor regression test scope estándar por surface

Complementario a R3: cada cambio TIPO genera test scope template auto:

| Surface change type | Auto-generated regression scope |
|---|---|
| New API route | E2E smoke `routes.test.ts` + auth/tenant isolation tests + response_model PII test |
| New SQLA model | Migration idempotency + tenant isolation in repo + soft delete behavior |
| New service method | Unit test happy + 1 edge + 1 adversarial + tenant filter |
| New LLM tool | Eval golden + prompt cache hit test + cost recording test + tenant_id passthrough |
| New BG worker | Idempotency test + retry behavior + observability event recording |
| New cron job | Schedule test + idempotency + skip when condition not met |
| New domain event | Outbox emission + at-least-once delivery + tenant_id propagation |
| New FE form | RHF + Zod schema test + autosave on-change + accessibility (semantic + keyboard) + Spanish neutro labels |
| New FE chart | Loading/error/empty state + multi-tenant currency + responsive |
| New FE route | E2E smoke + auth gate + 404 fallback |

Auditor checks: ticket touched type X → scope must include test categories Y. Si ticket missing → CHANGES_REQUESTED.

**Esfuerzo:** 3-4h table SSoT (`auditor-regression-scope-by-type.md`) + integration into auditor agents.

**Beneficio:** raise floor — bugs cross-cutting (PII leak, missing autosave, no auth) catch even when not explicit in ticket spec.

### Propuesta R19 — Auditor learn-from-failures loop

Cada caso `bug found post-merge` triggers learning:

1. PM ratifica bug post-mortem en `docs/process/auditor-misses/{date}-{bug-slug}.md`
2. Document: which check FAILED to catch + auditor checklist line that should have caught + proposed checklist amendment
3. PM amends `auditor-{backend,agentic,frontend}.md` agent definition with new check
4. Quarterly review: PM aggregates last 3-month auditor-misses/ → identifies systemic gaps

Schema doc:

```markdown
# Auditor Miss: {bug-slug}

**Date detected:** YYYY-MM-DD
**PR/Ticket origin:** PI-N S-N T-N
**Auditor verdict at merge:** APPROVED
**Bug class:** {tenant leak | PII exposure | missing migration | regression cross-surface | cost overrun | ...}

## What auditor missed
{1-paragraph}

## Auditor check that should have caught
- Category: {N}
- Specific check line: {quote}
- Why it didn't fire: {regex too narrow | scope too local | check too rare}

## Proposed amendment
{specific text addition to auditor-{X}.md}

## Status
- [ ] Amendment merged
- [ ] Regression test added (`test_auditor_catches_{bug_slug}.py`)
```

**Esfuerzo:** 1h schema. Ongoing: 30min per miss documented.

**Beneficio:** auditor mejora compositamente. Cada miss → check permanente.

### Propuesta R20 — Auditor adversarial mode (opcional para PRs ≥ M)

Cuando PR es high-stakes (touches `shared/`, agentic, billing, auth, deploy infra):
- Spawn auditor TWICE: normal + adversarial
- Adversarial agent prompt: "Find what the normal auditor missed. Try to break the implementation. Run scenarios outside happy path."
- Diff verdicts → if adversarial finds FAIL not in normal → escalate
- Cost: 2x auditor tokens for 5-10% PRs (filter by labels) → ~$50-100/month avg

**Esfuerzo:** 2h auditor adversarial agent definition + integration.

**Beneficio:** safety net for stakes PRs. Optional flag (`high_stakes: true` in PR.md or ticket field).

---

## R12-R20 priorizadas

| R | Área | Esfuerzo | Beneficio | Prioridad | PI |
|---|---|---|---|---|---|
| **R12** | #1 process_run_metrics infra | 4-6h | data-driven mejoras + validate R1-R9 ROI | 🔴 Alta | PI-13 |
| **R14** | #4 skill audit + decommission | 6h | -10-20% prompt overhead + cognitive clarity | 🟡 Media | PI-13 |
| **R16** | #5 pattern-memory skill | 2h skill + 8-12h seed patterns | quality consistency + onboarding faster | 🟡 Media | PI-13 |
| **R18** | #6 regression scope by type | 3-4h | raise auditor floor cross-cutting | 🔴 Alta | PI-13 |
| **R19** | #6 learn-from-failures loop | 1h schema + ongoing | composite auditor improvement | 🟡 Media | PI-14+ |
| **R13** | #1 cost tracking table | 2h post R12 | enable PI cost queries | 🟢 Baja | PI-14+ |
| **R15** | #4 skill SSoT registry | 1h post R14 | clean up CLAUDE.md routing tables | 🟢 Baja | PI-13 |
| **R17** | #5 auto-pattern extraction | 6-8h | catch latent reusable code | 🟢 Baja | PI-14+ |
| **R20** | #6 auditor adversarial mode | 2h | safety net stakes PRs | 🟢 Baja | PI-14+ (opcional) |

**Recomendación PM:** PI-13 = R12 + R14 + R16 + R18 (4 mejoras, ~15-25h trabajo aggregate). R13/R15/R17/R19/R20 = backlog continuous improvement.

---

## Sinergias entre áreas

- **R12 (metrics) ↔ R14 (skill audit):** metrics revelan skill usage real → audit más informed
- **R12 (metrics) ↔ R20 (adversarial mode):** metrics permiten cost-control adversarial spend
- **R16 (pattern-memory) ↔ R18 (regression scope):** patterns library + scope template = test scaffolding automático
- **R19 (learn-from-failures) ↔ R18 (regression scope):** failures alimentan scope template (catch lo que faltó)
- **R14 (skill audit) ↔ R16 (pattern-memory):** decommissioning skills exposes patterns que vivían en SKILL.md → migrate to pattern-memory

**Conclusión:** R12 + R14 + R16 + R18 forman cluster cohesivo. Implementar PI-13 los 4 maximiza benefit cross-amplification.

---

## Anti-patterns a evitar implementando R12-R20

- ❌ Métricas sin baseline (R12) — capture pre-R1-R9 baseline ASAP from existing transcripts antes que perder data
- ❌ Decommission skills sin deprecation window (R14) — algo lo invocaba indirectamente
- ❌ Pattern-memory que duplica official docs (R16) — patterns son LATAM-specific / Nicolify-specific, no `tessl__fastapi` re-write
- ❌ Regression scope by type (R18) que se vuelve excessive — list 5-7 categorías por type, no 25
- ❌ Auditor adversarial mode (R20) en TODO PR — costo explota; usar flag selectivo

---

## Referencias

- `docs/process/process-improvement-handoff-2026-05-05.md` — origen R1-R11 + 10 áreas sugeridas
- Sesión origen 2026-05-04/05: R1-R9 + A0 implementadas
- Commits sesión: `git log --oneline 864b0e31..HEAD --grep="^feat\|^docs(rules\|^docs(templates\|^docs(pm\|^docs(pi-12-T6b"`
</content>
</invoke>