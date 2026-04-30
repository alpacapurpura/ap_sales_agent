# PR-Folder Template

> Template canónico para todo PR nuevo. Cada PR vive en su propia carpeta auto-contenida.

## Cuándo copiar este template

PM crea nuevo PR → copy este folder a `pis/active/PI-N-{theme}/sprints/SN-*/prs/PR-{n}-{slug}/`.

## Estructura

```
prs/PR-{n}-{slug}/
├── PR.md                       ← PM (problema, soluciones, copilot-first, agentes)
├── design.md                   ← (opcional, agregado post-UX) UI insights consolidados
├── mockups/                    ← (opcional, agregado post-UX) screenshots, links
├── CONTRACT.md                 ← architect (schema + interface + retry policy)
├── UI-SPEC.md                  ← ux-flow-architect (si aplica UI)
├── prompts/
│   ├── 01-architect-start.md   ← PM pre-coce prompt para architect
│   ├── 02-builder-start.md     ← PM pre-coce prompt para builder (BE/FE/agentic)
│   ├── 03-auditor-start.md     ← PM pre-coce prompt para auditor
│   └── 04-pm-close.md          ← PM pre-coce prompt para volver a PM cerrar loop
├── phases/                     ← (opcional, solo PRs muy amplios) sub-fases
│   └── phase-N-{slug}/
│       ├── plan.md
│       ├── completion-checklist.md
│       └── learnings.md
├── IMPL-LOG.md                 ← builder appendea decisiones implementación
├── REVIEW.md                   ← auditor (findings + score)
└── RESULT.md                   ← PM (cierre: outcome real, surface entregada, métricas)
```

## Estados PR (en `PR.md`)

`discovery` → `ready` → `in-progress` → `review` → `shipped`

PM commitea cambio de Estado **inmediato** (claim by commit). Otra sesión paralela ve estado actualizado al hacer `git pull`.

## Reglas

1. **Quien escribe qué:**
   - `PR.md`, `RESULT.md`, `prompts/*` → PM
   - `CONTRACT.md` → architect
   - `UI-SPEC.md`, `design.md`, `mockups/` → ux-flow-architect (consolidado por PM)
   - `IMPL-LOG.md` → builder (BE/FE/agentic)
   - `REVIEW.md` → auditor

2. **Protocolo `@pm` comment:** cada agente builder/UX/auditor termina su última respuesta con:
   ```
   <!-- @pm: [phase] done. Próximo paso: ejecutar prompts/{NN}-{next}-start.md o ejecutar /pm "PR-{n} {phase} done" -->
   ```

3. **PM scope:** PM nunca escribe código, solo orquesta. PM lee outputs filesystem y consolida en `RESULT.md` al cierre.

4. **Sin folder `phases/`** salvo PR muy amplio (≥3 sub-deliverables independientes con riesgo distinto). Default = sin phases.

5. **`mockups/`** solo si UX participa. Cero archivos sueltos.

## Cómo usar

```bash
# PM en sesión /pm
cp -r docs/pm-nico/process/pr-folder-template \
      docs/pm-nico/pis/active/PI-N-{theme}/sprints/SN-*/prs/PR-{n}-{slug}
cd docs/pm-nico/pis/active/PI-N-{theme}/sprints/SN-*/prs/PR-{n}-{slug}
# editar PR.md con contenido real
# editar prompts/* con paths/contexto real del PR
# git add + commit "feat(pm): create PR-N skeleton"
```
