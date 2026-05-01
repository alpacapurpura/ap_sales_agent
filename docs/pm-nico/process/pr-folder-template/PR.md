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

## Existing systems audit (MANDATORY — bloque con paths grepped)

> **NO NEW LAYER rule**: si ya existe en el codebase un factory + protocol + providers que hace lo que este PR propone, EXTENDÉ no DUPLIQUES.
> Origen rules:
> - PR-3 PI-2 S2 audit failure 2026-04-30 (introdujo `model_config.py + DeepSeekLLMProvider + provider_factory.py` paralelos a `core/config.py + shared/infrastructure/llm/router.py + providers/`).
> - PR-1 PI-1.1 hotfix 2026-05-01 (builder agentic creó `modules/sales_agent/observability/recording/turn_envelope.py` mirror de `modules/copilot/observability/recording/turn_envelope.py` existente — REVERT obligatorio).
>
> **PM no commitea PR-folder con esta sección incompleta o vacía.** Auditor FAIL si claims sin evidence.

Para CADA subsystem que el PR toca (LLM routing, cache, queue, auth, observability, billing, rate-limit, channel format, callback handler, cost/pricing, FX, etc.):

### 1. Grep cross-module obligatorio (output completo embedido)

Ejecutar y pegar SALIDA REAL aquí (no resumen):

```bash
# 1a. Buscar archivos con nombre o patrón similar al que vas a crear:
find /home/chris/AISALESHT/backend/src -name "<filename>.py" 2>&1
find /home/chris/AISALESHT/frontend/src -name "<filename>.ts*" 2>&1

# 1b. Buscar clase/función/protocol equivalente en shared y modules paralelos:
grep -rn "class <ClassName>\|def <function_name>" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null

# 1c. Buscar imports cross-module del subsystem:
grep -rn "from src.shared.<subsystem>\|import <subsystem>" /home/chris/AISALESHT/backend/src/ 2>/dev/null | head -20

# 1d. Consultar inventario canónico shared abstractions:
cat /home/chris/AISALESHT/.claude/rules/anti-duplication.md | grep -A 1 "<subsystem keyword>"
```

**Salida grep:**

```
[PASTE REAL OUTPUT HERE — paths + line numbers]
```

### 2. Inventario de existing patterns encontrados

| Pattern existente | Path:line | Visible para mi módulo? | Status |
|---|---|---|---|
| ej: `BaseObservabilityContext` | `shared/agent_observability/recording/turn_envelope.py:142` | sí cross-module exception copilot | exists, EXTEND-via-inheritance |
| ej: `FXResolver()` factory | `shared/agent_observability/cost/fx_resolver.py:38` | sí | exists, USE-AS-IS via `.default()` |

### 3. Decisión explícita por sistema (EXTEND / LIFT / NEW)

| Sistema | Decisión | Justificación con path:line |
|---|---|---|
| ej: turn envelope sales_agent | **EXTEND** vía herencia desde shared base | `shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext` ya define lifecycle. Sub-class añade only sales-specific fields |
| ej: FX resolver call site | **USE-AS-IS** | `shared/agent_observability/cost/fx_resolver.py::FXResolver.default()` factory exists |

**Categorías permitidas:**
- **EXTEND** (preferred): cómo ampliar el existente sin breaking changes
- **LIFT-TO-SHARED** (cuando 2+ módulos lo necesitarían): primer commit lift abstracción a `shared/`, después módulos consumen
- **REPLACE** (riesgo alto): justificación cuantitativa por qué el existente debe morir + plan migración
- **NEW** (último recurso): evidencia path:line que ninguno de los encontrados sirve + por qué

### 4. Si decisión es NEW

Bloque obligatorio "Por qué los existentes no sirven":

- ¿Qué intentaste extender primero? Path:line del existente.
- ¿Por qué falló extend? Razón técnica concreta (no "no me gusta el API").
- ¿Criterio Chris satisfecho? Escala 1000+ tenants, costo, calidad invariantes.

### 5. Auditor enforcement

Auditor Cat 12 (mirror detection) busca duplicación post-implement. Si encuentra archivo con name+structure similar en módulo paralelo sin justificación NEW → verdict FAIL.

(skip esta sección entera SOLO si grep en sección 1 devuelve cero resultados Y inventario `rules/anti-duplication.md` no lista subsystem — no es atajo, es consecuencia de evidencia)

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
