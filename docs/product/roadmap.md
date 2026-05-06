---
last_updated: 2026-05-05
last_updated_by: /pm
audit_freq: weekly
next_audit: 2026-05-12
schema: now-next-later (Bastow)
owner: /pm
links:
  vision: ./vision.md
  index: ./INDEX.md
  modules: ./modules/
  legacy_roadmap: ../pm-nico/roadmap.md
---

# Nicolify Roadmap

> Modelo **Now / Next / Later** (Bastow). Sin fechas falsas. Promesa = dirección, no commit.
> Owner único: `/pm`. Update obligatorio en `07-merge.md` checklist + bootstrap weekly audit.
> Legacy PIs (PI-3..11) viven en paradigma viejo `docs/pm-nico/` — referenced abajo "Legacy active", cierran allá.

## Now — En ejecución (paradigma SDD nuevo)

### PI-12 — Sales Agent Eval Foundation
- **Outcome:** cada PR `modules/sales_agent/` gradeado auto vs voice fidelity (≥0.7) + pass^k (≥0.5) + cost cap. CI bloquea regressions de voz/costo/no-hallucination.
- **Why now:** `gap-report-2026-05-04-group-c.md` flag CRÍTICO — 6 agentic stories sales_agent declaradas sin pass^k tracking, sin goldens checked-in, sin voice fidelity grader runs. Sin esto, cualquier cambio sales_agent es ruleta rusa de voz tenant + costo.
- **Status:** EXECUTING (S1 in-progress, 2/9 stories audit-passed: `eval-runner-foundation` Wave 2, `litellm-canonicalization` Wave 3).
- **Sprints:** 4 (S1 eval-runner activo, S2 goldens-personas / S3 voice-fidelity-gate / S4 adversarial blocked deps).
- **Target end:** 2026-06-08 (~5 semanas).
- **Risk:** voice fidelity grader nondeterministic (LLM judge); mitigation = calibrate vs experto humano cada 50 goldens.
- **Links:**
  - PI: `docs/projects/active/PI-12-sales-agent-eval-foundation/PI.md`
  - Checkpoint: `docs/projects/active/PI-12-sales-agent-eval-foundation/checkpoint.md`
  - Origen: `docs/process/gap-report-2026-05-04-group-c.md`

## Now — Legacy active (paradigma viejo `pm-nico/`)

> Cierran en `pm-nico/`. NO migran retroactivo. Listed acá solo para visibilidad cap concurrente.

| PI | Theme | Estado | Link |
|---|---|---|---|
| PI-5 | Copilot multicanal — Telegram MVP | S2 shipped, S3 pending | `docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/PI.md` |
| PI-11 | Backend quality guardrails | S1 shipped (PRs 1-4 done) — pendiente cierre formal | `docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/PI.md` |
| PI-4 | Brand evolutive maintenance (rolling) | active, S1 in-progress | `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/PI.md` |

## Next — Priorizado, no iniciado

### PI-13 — Copilot eval suite + adversarial Telegram (TBD nombre)
- **Outcome:** orchestrator-level eval para copilot module (no solo classifier+summarizer goldens existentes). Adversarial scenarios Telegram (jailbreak via doc upload, prompt injection cross-channel).
- **Why next:** `gap-report-2026-05-04-group-c.md` HIGH — copilot eval PARCIAL. Pattern eval reusable de PI-12 (runner + pass^k + cost cap). Sin esto, copilot bug surface invisible.
- **Bloqueado por:** PI-12 cierre (reuse runner infra + voice fidelity grader pattern).
- **Status:** discovery TBD.
- **Estimate:** ~4-5 semanas (similar shape a PI-12).

### PI-9 — Growth Studio architecture homologation (legacy)
- **Outcome:** registries SSoT + StageDispatcher + actions/schemas/tiers consolidación. Refactor estructural FE para escalabilidad multi-stage.
- **Why next:** desbloqueado 2026-05-01 (PI-8 shipped). Bloquea PI-10 (UX redesign) que depende de arquitectura clean.
- **Bloqueado por:** asignación dev (Opus architect requerido).
- **Status:** discovery, plan macro pendiente refine.
- **Link:** `docs/pm-nico/pis/active/PI-9-growth-studio-architecture/PI.md`

### PI-3 — Sales agent improvement (legacy, pre PI-12)
- **Outcome:** mejoras post-redesign 2026-04 (cards, follow-up, payment reminders).
- **Why next:** desplazado por PI-12 (eval foundation) — sin eval suite, improvements no tienen safety net. Re-priorizar post PI-12 cierre.
- **Status:** discovery placeholder.
- **Link:** `docs/pm-nico/pis/active/PI-3-sales-agent-improvement/PI.md`

## Later — Discovery / opportunities

### Opportunities formalizadas
> Vacío todavía. `docs/product/opportunities/` por crear cuando Chris valide próxima discovery.

### Ideas pool (`docs/product/ideas/`)
- **calendario-comercial** — comercial calendar events module evolution
- **metricas-atraccion** — attraction stage metrics expansion

### Legacy backlog `pm-nico/` no migrado
- PI-10 — Growth Studio UX homologation (bloqueado por PI-9)

## Recently shipped (90d rolling — paradigma legacy)

| PI | Theme | Closed | Archive |
|---|---|---|---|
| PI-1 | Campaigns module — Foundation + Telegram MVP | 2026-04-30 | `docs/pm-nico/pis/archive/PI-1-campaigns-module/retro.md` |
| PI-1.1 | PI-1 post-mortem hotfixes | 2026-05-01 | `docs/pm-nico/pis/archive/PI-1.1-pi1-post-mortem/retro.md` |
| PI-7 | App stability restore (brand adapter + LiteLLM) | 2026-05-01 | `docs/pm-nico/pis/archive/PI-7-app-stability-restore/retro.md` |
| PI-8 | Growth Studio stability (drawer + bowtie + offset) | 2026-05-01 | `docs/pm-nico/pis/archive/PI-8-growth-studio-stability/retro.md` |

## Cancelled / Deprecated

> (none)

---

## Update protocol

### Trigger 1 — Per merge story (mandatory)
`/pm` ejecuta `07-merge.md` checklist:
1. Si story merged completa último gap del PI → PI status flip a DONE
2. Move PI entry from Now → Recently shipped
3. Promote first Next entry → Now
4. Update `last_updated` field + bump `next_audit` (+7d)

### Trigger 2 — Nuevo PI ratificado
`/pm` crea `docs/projects/active/PI-{N}/PI.md` →
- Agrega entry en Next (no Now hasta arrancar EXECUTING)
- Cita `why_next` con link a opportunity / gap-report origen

### Trigger 3 — Opportunity validada
Chris + `/pm` ratifican opportunity con scope mínimo →
- Promote desde Later → Next placeholder

### Trigger 4 — Bootstrap weekly audit
`/pm` cada activación:
1. `ls docs/projects/active/` → comparar contra Now
2. `git log --since="7 days ago" --grep="^docs(pi-"` → detectar merges no reflejados
3. Si mismatch → STOP, reportar Chris, fix antes proceder

### Trigger 5 — Capability status drift
Pre-commit hook `scripts/reconcile_capabilities.py --check` (R32 2026-05-05) bloquea commits con drift cap status. Roadmap consume cap statuses confiables.

## Anti-patterns

- ❌ Story-level detail (vive en `stories/{m}/{id}.yaml`)
- ❌ Implementation details (vive en `03-arch-*.md`)
- ❌ Daily standup updates (vive en `checkpoint.md`)
- ❌ Métricas tiempo-real / burndown (roadmap = strategic, no tracker)
- ❌ Wishlist sin validar (vive en `ideas/`)
- ❌ Estimaciones pasadas embebidas (solo target_end actual)
- ❌ Decisiones cardinales (vive en `learnings.md`, link no copia)
- ❌ Gantts (markdown plano; DAG separado en `dependency-map.md` si necesario)
- ❌ Update solo at quarter-end (drift garantizado — usar Triggers 1-5)
