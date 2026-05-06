# Prompt — PM Execute (PR-4 — PM directo, no builder técnico)

> PR-4 = PM directo. NO spawn builder ni auditor técnico.
> Pre-requisito: PR-3 shipped (regla `.claude/rules/anti-default-flip-audit.md` existe + arch fitness test existe).

## Acciones (PM las ejecuta directo en sesión)

### Pre-flight

1. Verificá PR-3 shipped:
   ```bash
   ls /home/chris/AISALESHT/.claude/rules/anti-default-flip-audit.md
   ls /home/chris/AISALESHT/backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py
   ```
   Si alguno NO existe → STOP. PR-3 todavía no shipped. Esperá ship + retry.

2. Read PR.md de PR-4 completo + cross-link to PR-3 RESULT.md.

3. Read agentes existing:
   - `.claude/agents/nicolify-architect.md`
   - `.claude/agents/nicolify-backend.md`
   - `.claude/agents/nicolify-agentic.md`
   - `.claude/agents/nicolify-backend-auditor.md`
   - `.claude/agents/nicolify-agentic-auditor.md`
   - `.claude/skills/pm/SKILL.md`
   - `.claude/rules/tdd-mandatory.md`
   - `docs/pm-nico/process/process-learnings.md`

### Step 1 — Update `nicolify-architect.md`

Identificar sección apropiada (típicamente al final del prompt template del agente o en sección "Workflow"). Insertar bloque "Default-flip audit" según PR-4/PR.md § Step 1.

### Step 2 — Update `nicolify-backend.md`

Insertar `Step 0.5 — Default-flip detection` en sección "Step 0 GATE" o equivalente.

### Step 3 — Update `nicolify-agentic.md`

Mismo Step 0.5, adaptado a context agentic.

### Step 4 — Update `nicolify-backend-auditor.md`

Identificar tabla de categorías review (Cat 1-13 actual). Agregar Cat 14 "Default flip side-effect coverage" según PR-4/PR.md § Step 4.

### Step 5 — Update `nicolify-agentic-auditor.md`

Mismo Cat (numerar consistente con schema agentic, leer schema actual primero).

### Step 6 — Update `pm` SKILL.md

Agregar:
- Sección "Default flips audited" en PR.md template (o dentro de pr-folder-template/PR.md si template canónico).
- Antipattern entry en lista existing.

### Step 7 — Update `tdd-mandatory.md`

Append sección "Default flag flips" según PR-4/PR.md § Step 7.

### Step 8 — Update `process-learnings.md`

Append entry 2026-05-04 según PR-4/PR.md § Step 8.

### Step 9 — Optional pr-folder-template/PR.md update

Si pm SKILL.md template referencia `pr-folder-template/PR.md`, evaluar si template canónico necesita bloque "Default flips audited" pre-cocido. Actualizar si aplica.

### Step 10 — Self-check cross-references

```bash
# Verificar cross-references válidos:
grep -n "anti-default-flip-audit.md" /home/chris/AISALESHT/.claude/agents/nicolify-*.md /home/chris/AISALESHT/.claude/skills/pm/SKILL.md /home/chris/AISALESHT/.claude/rules/tdd-mandatory.md
grep -n "test_no_legacy_eventbus_mock_when_outbox_on" /home/chris/AISALESHT/.claude/agents/nicolify-*-auditor.md
```

Confirmar todos los links apuntan a paths que existen.

### Step 11 — Commit + push

```bash
cd /home/chris/AISALESHT
git status --short
git add .claude/agents/nicolify-architect.md .claude/agents/nicolify-backend.md .claude/agents/nicolify-agentic.md
git commit -m "docs(agents): cement default-flip audit in builder/architect prompts (PI-11 PR-4)"
git add .claude/agents/nicolify-backend-auditor.md .claude/agents/nicolify-agentic-auditor.md
git commit -m "docs(agents): add Cat default flip side-effect coverage to auditors (PI-11 PR-4)"
git add .claude/skills/pm/SKILL.md
git commit -m "docs(pm-skill): add Default flips audited block to PR.md template (PI-11 PR-4)"
git add .claude/rules/tdd-mandatory.md
git commit -m "docs(rules): extend tdd-mandatory with Default flag flips section (PI-11 PR-4)"
git add docs/pm-nico/process/process-learnings.md
git commit -m "docs(pm): document default-flip pattern as process learning (PI-11 origen)"
git push origin development
```

### Step 12 — Escribir RESULT.md

Lista archivos updated + cross-references validados + lineage referenciado a PR-1 + PR-3.

### Step 13 — Cambiar Estado: shipped en PR-4/PR.md

### Step 14 — Append decisión PI-11/decisions.md

```
2026-05-04 — PR-4 shipped: agentes/skills/rules cementan default-flip audit. Defense-in-depth full activa: layers 1-6.
```

### Step 15 — Append learning S1-test-integrity-and-coverage/learnings.md

Patrón "default flag flip = side-effect call path change" cementado en agents/skills/rules. Reusable para futuros flags side-effect (LITELLM_PROXY_ENABLED, USE_DEEPAGENTS_*, etc.). Costo evitado: replica per-deploy de PI-11 origen.

## Próximo paso

Si PR-1 + PR-3 + PR-4 shipped → cierre sprint S1 (PR-2 separate post):
```
Próximo paso (sprint cierre opcional si PR-2 todavía no abierto): ejecutar /pm "cerrar sprint S1 + open PR-2 builder"
```

O directo PR-2:
```
Próximo paso: ejecutar `docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules/prompts/02-builder-start.md`
```
