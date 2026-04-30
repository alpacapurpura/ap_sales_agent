# PR-{N}-{slug}

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-N-{slug} |
| Sprint padre | S{N}-{slug} |
| PI padre | PI-X-{theme} |
| Estado | discovery \| ready \| in-progress \| review \| shipped |
| Tipo | infra \| feature \| bug \| refactor \| research |
| Esfuerzo | XS \| S \| M \| L |
| Owner PM | /pm |
| Claimed by session | — (cuando in-progress, anotar fecha + módulo trabajo paralelo si aplica) |

## Problema (user-facing)

{1-2 líneas. JTBD si aplica.}

## Outcome esperado

{Qué cambia para el user. Métrica si medible.}

## Walking skeleton (mínimo viable cohesivo)

{Lo más chico que entrega valor cohesivo. Aprovechar Opus 4.7[1M] = scope amplio cuando es cohesivo. NO splittear por miedo al contexto.}

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A | ... | ... | ELEGIDA |
| B | ... | ... | descartada porque... |

## Validación técnica preliminar (Technical Sanity Check)

> PM spawned `Explore` o `nicolify-architect` (read-only) durante discovery. Brief sintético abajo. CONTRACT formal lo escribe architect en su fase.

- Modules afectados: ...
- Blockers conocidos: ...
- Tiempo estimado: ...
- Alternativas técnicas: ...

(skip si scope XS/S sin riesgo arquitectónico)

## Existing systems audit (architect-mandatory ANTES de proponer nueva capa)

> **NO NEW LAYER rule**: si ya existe en el codebase un factory + protocol + providers que hace lo que este PR propone, EXTENDÉ no DUPLIQUES. Origen rule: PR-3 PI-2 S2 audit failure 2026-04-30 (introdujo `model_config.py + DeepSeekLLMProvider + provider_factory.py` paralelos a `core/config.py::Settings.get_model/get_provider_for_role` + `shared/infrastructure/llm/router.py + providers/` ya existentes). Capa duplicada = código orphan + drift + deuda escala.

Para cada subsystem que el PR toca (LLM routing, cache, queue, auth, observability, billing, rate-limit, etc.):

- [ ] **Grep cross-module obligatorio**:
  - `grep -rn "settings\.get_\|<subsystem keyword>" src/core/ src/shared/` (sistema global existente)
  - `grep -rn "from src.core.config\|from src.core.enums" src/modules/<target>/` (ya consumido)
  - `find src/ -name "*.py" -path "*<subsystem>*"` (todos los archivos relacionados)
- [ ] **Listar enums + config classes + factories + protocols + providers** encontrados (con paths exactos).
- [ ] **Decisión explícita por sistema encontrado**:
  - **EXTEND** (preferred): cómo ampliar el existente sin breaking changes
  - **REPLACE** (riesgo alto): justificación cuantitativa por qué el existente debe morir + plan migración
  - **NEW** (último recurso): evidencia que ninguno de los encontrados sirve + por qué
- [ ] Si NEW → bloque "Por qué los existentes no sirven" con código real referenciado (path:line) + criterio Chris (escala 1000+ tenants, costo, calidad invariantes).

(skip solo si grep cross-module devuelve cero resultados — no es scope ni atajo)

## Decisiones diferidas (explícitas)

- {Qué NO se resuelve hoy y cuándo se aborda.}

## Out of scope

- ...

## Copilot-first checklist

- [ ] ¿Operable conversacional desde copilot? (default Sí)
- [ ] ¿Qué tools nuevos requiere? (lista)
- [ ] ¿Cards/UI nueva? (lista)
- [ ] Si NO copilot → razón documentada

## Agentes / skills recomendados

(Ver `process/agent-routing-matrix.md`)

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` | `prompts/01-architect-start.md` | `CONTRACT.md` |
| UX (opcional) | `ux-flow-architect` | (PM crea ad-hoc si aplica) | `UI-SPEC.md` + `mockups/` |
| Implementation | `nicolify-{backend\|frontend\|agentic}` | `prompts/02-builder-start.md` | code + tests + `IMPL-LOG.md` |
| Audit | `nicolify-{backend\|frontend}-auditor` | `prompts/03-auditor-start.md` | `REVIEW.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/{m}.md` update |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Tabla DB | ... | nueva / alter |
| API endpoint | ... | nuevo / modificado |
| Domain type | ... | nuevo / modificado |
| FE component | ... | nuevo / modificado |
| current-state/ | `current-state/{módulo}.md` | append capability con lineage |

## Tests requeridos (TDD)

- `tests/.../test_*.py` — qué cubre

## Aceptación

- [ ] Tests verdes
- [ ] Lint/type check verdes
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` sin findings críticos
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/{módulo}.md` actualizado con capability lineage
- [ ] Decisiones registradas en `decisions.md` PI

## Riesgos

| Riesgo | Mitigación |
|---|---|
| ... | ... |
