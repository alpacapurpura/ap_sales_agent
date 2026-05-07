---
story_id: maintenance-skill-sales-agent-audit
surface: BE
sub_architect: /architect (orchestrator, BE inline — no /architect-be sub-spawn por trivialidad de surface)
arch_version: 1
last_modified: 2026-05-06T19:45Z
links:
  spec: 01-spec.md
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  skill_target: ../../../../.claude/skills/sales-agent-expert/
  rules:
    - ../../../../.claude/rules/anti-duplication.md
    - ../../../../.claude/rules/spanish-text.md
    - ../../../../.claude/rules/parallel-safety.md
    - ../../../../.claude/rules/git-safety.md
    - ../../../../.claude/rules/tdd-mandatory.md
---

## Decisión arquitectónica clave

Esta es una **doc-engineering story sin runtime impact**. El surface técnico se limita a (a) un test pytest nuevo que mecaniza el audit como gate de regresión y (b) ediciones a 5 archivos markdown del skill. Cero cambios en `backend/src/`, `frontend/src/` o migrations. La complejidad radica en el **workflow del audit** (4 pasadas) y la **política de utility verdicts** que el dev-team debe ejecutar cuidadosamente — NO en la arquitectura técnica del test.

**Decisión cardinal (AD1):** un único archivo de test `backend/tests/scripts/test_skill_sales_agent_audit.py` con N funciones de test (una por scenario del 01-spec.md), parseo del skill via regex/AST de markdown, resolución de paths via filesystem `Path.exists()` + grep AST cross-codebase para imports `shared.agent_observability.*`. Sin nuevas abstracciones, sin nuevas tablas, sin nuevos servicios. Patrón de precedente: `backend/tests/scripts/test_pre_commit_hook.py` (test sobre artefactos no-runtime).

**Decisión cardinal (AD2):** estructura del skill preservada — `SKILL.md` + `references/{conversation-stages,humanization-rules,sales-agent-brand-voice,tool-patterns}.md`. NO se crean nuevos archivos de reference. NO se mergea ni se splittea archivos existentes. Las modificaciones internas a cada archivo siguen política Q4 ratificada: utility verdicts KEEP/UPDATE/DELETE/RESTRUCTURE con preservación verbatim en `T-1-impl-log.md` para todo lo que cae bajo DELETE/RESTRUCTURE.

**Decisión cardinal (AD3):** dos secciones nuevas en `SKILL.md` (estricto, ubicación entre "Decisiones cross-fase" existente y "SSoT vivos" existente):
- `## Surfaces compartidas con copilot (consumers shared/agent_observability)` — bullets de 1 línea, formato `- shared.agent_observability.{subsystem} → consumed by modules/sales_agent/{file}`
- `## Decisiones cardinales últimos 60 días` — bullets de 1 línea con date + decisión + reference (story id / commit short hash / learning entry)

**Decisión cardinal (AD4):** la tabla `Utility verdicts` (cobertura 100% de secciones H2/H3 + references files) NO vive en el skill — vive en `T-1-impl-log.md`. Razón: el skill consumido por `/architect` y `/dev-team` debe permanecer denso y útil; los verdicts son metadata de proceso del audit, no contenido vivo del skill.

**Decisión cardinal (AD5):** convención marker `OBSOLETO:` — line-prefix mayúsculas con dos puntos + comentario inline post-marker (regex `^OBSOLETO:.+—.+$` o equivalente con explicación de reemplazo). Aplica a paths citados que NO existen pero queremos preservar trazabilidad histórica (e.g., paths renombrados, schemas removidos por refactor reciente).

**Decisión cardinal (AD6):** cero `production_code` — owner pool del único ticket T-1 = `[qwen-opencode, claude-sonnet]`, Opus NO requerido (R23). Razón: aunque el contenido auditado refiere al módulo `sales_agent` (agentic), el trabajo del audit es doc-engineering + test pytest sobre filesystem + parsing markdown. Ni una línea de código modifica runtime agentic.

## Surface diff (BE)

### Endpoints nuevos / modificados

Ninguno.

### DTOs

Ninguno.

### Domain entities / VOs

Ninguno.

### Migrations

Ninguna.

### Servicios + Repos

Ninguno.

### Eventos emitidos / consumidos

Ninguno.

### Tests requeridos

| Test file | Funciones (scenarios cubiertos) | Tipo |
|---|---|---|
| `backend/tests/scripts/test_skill_sales_agent_audit.py` | 5 funciones — ver §Test design abajo | pytest unit + filesystem assertions |

### Test design (detalle)

**Path:** `backend/tests/scripts/test_skill_sales_agent_audit.py`

**Imports + constantes top-level:**
```python
"""Tests para el audit del skill sales-agent-expert (story maintenance-skill-sales-agent-audit).

Verifica que SKILL.md + references/*.md mantengan coherencia con código vivo:
1. paths citados existen (o tienen marker OBSOLETO)
2. surfaces shared/agent_observability/* consumidas están documentadas
3. zero contradicciones cross-archivo dentro del skill
4. impl-log tiene secciones obligatorias

# voseo-allowed: este test parsea contenido del skill que cita voseo del tenant verbatim
# como referencia documental (ver .claude/rules/spanish-text.md § sales_agent excepción).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "sales-agent-expert"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
IMPL_LOG = REPO_ROOT / "docs" / "product" / "stories" / "maintenance-skill-sales-agent-audit" / "T-1-impl-log.md"
SALES_AGENT_SRC = REPO_ROOT / "backend" / "src" / "modules" / "sales_agent"
SHARED_OBS = REPO_ROOT / "backend" / "src" / "shared" / "agent_observability"

# Helpers (parsers, path resolvers) abajo.
```

**Funciones de test (1 por scenario + 1 positive control):**

| Test function | Scenario covered | Mecánica |
|---|---|---|
| `test_skill_paths_resolve_or_have_obsolete_marker` | happy (1) | Parse SKILL.md + cada `references/*.md`. Para cada match de patrón path/clase (regex curado para capturar `backend/src/...`, `modules/{m}/...`, `shared/{...}`, `class {Name}`, etc.), verificar que `Path.exists()` o que la línea contenga prefix `OBSOLETO:`. Falla con lista de paths no resueltos. |
| `test_obsolete_marker_has_inline_reason` | negative (2) | Para cada línea con `OBSOLETO:`, regex assert que existe comentario post-marker con separador `—` o `:` o `→` y razón non-empty. Falla con lista de líneas marker sin razón. |
| `test_shared_observability_consumers_documented` | edge (3) | AST scan de `backend/src/modules/sales_agent/**/*.py` (usando `ast.parse`) para extraer todos los imports que matcheen `from src.shared.agent_observability` o `from shared.agent_observability`. Compara set extraído vs set documentado en sección `## Surfaces compartidas con copilot` de SKILL.md (parsed via regex). Set equality assertion. |
| `test_skill_no_self_contradiction` | adversarial (4) | Enumera ≥4 invariantes canónicas (lista hardcoded en el test): voseo, anti-duplication, §3 protected surfaces, PII regex stance. Para cada invariante, define 2-3 strings esperados/prohibidos cross-archivo. Por ejemplo voseo: SKILL.md debe contener "voseo del tenant respetado" Y `references/sales-agent-brand-voice.md` debe contener `personality_profiles.system_instruction` Y NO debe contener "evitar voseo en outputs" (literal). Falla con lista de contradicciones detectadas. |
| `test_contradiction_detector_flags_synthetic_injection` | adversarial (4) — positive control | Crea copia tmp del skill en `tmp_path`. Inyecta string contradictorio sintético (e.g., en el archivo copia inserta `evitar voseo en outputs sales_agent`). Llama al detector con base path=tmp; assert que detecta la contradicción. Garantiza que el grader NO es no-op. |
| `test_impl_log_has_required_sections` | happy (1) — gate adicional | Verifica que `T-1-impl-log.md` exista y contenga los 4 headers H3 obligatorios: `### Claims removed (archived)`, `### Claims updated`, `### Claims added`, `### Utility verdicts`. Si el log no existe aún (build mid-flight), el test marca `xfail` solo durante state=developing; en state=developed debe pasar GREEN. |
| `test_utility_verdicts_cover_all_skill_sections` | happy (1) — gate adicional | Parse SKILL.md secciones H2/H3 + cada archivo references/*.md como "secciones globales". Compara con tabla `### Utility verdicts` en impl-log. Set equality. |

**Coverage minimum:** N/A — tests live in `tests/scripts/`, no participan del coverage threshold del módulo (43%).

**Determinismo:** todos los tests son puros — leen filesystem, no DB, no network, no LLM. `pytest --count=3` debe pasar idéntico.

## Surface diff (FE)

N/A — story no toca FE.

## Surface diff (Agentic)

N/A — story es doc-engineering sobre skill que documenta agentic, pero el audit en sí no toca runtime agentic ni production code agentic. Per R23, surface=BE + production_code=false → owner pool sonnet/qwen, Opus NO requerido.

## Cross-cutting concerns

- **Tenant isolation:** N/A (no DB queries).
- **Idempotency:** test idempotente (pure filesystem reads).
- **Rate limiting:** N/A.
- **Caching:** N/A.
- **Backwards compatibility:** skill consumers (`/architect`, `/dev-team`, `/auditor`, builders) leen el skill on-demand — cambios a content no rompen contratos sintácticos. Cambios de estructura (rename/split files) están explícitamente fuera de scope (AD2).

## Surfaces compartidas con copilot (sirve de pre-research para el dev-team — NO sustituye el audit)

El dev-team durante el audit DEBE ejecutar AST scan completo. Esta lista es **input de trabajo**, no output final:

| shared subsystem | sales_agent consumer (paths probables — verificar) | Documentado en skill actual? |
|---|---|---|
| `shared.agent_observability.recording.base_callback_handler` | `modules/sales_agent/observability/recording/callback_handler.py` (probable) | Sí (SKILL.md decisiones cross-fase línea 70 cita `BaseAgentCallbackHandler` Template Method) |
| `shared.agent_observability.cost.calculator` | `modules/sales_agent/observability/recording/callback_handler.py` (vía cost_recorder) | Parcial (SKILL.md menciona "tier pricing >200k") |
| `shared.agent_observability.cost.cost_recorder` | idem | NO documentado explícito post canonicalization (story shipped 2026-05-06) |
| `shared.agent_observability.cost.fx_resolver` | probable consumer en cost path | NO documentado |
| `shared.agent_observability.cost.pricing_resolver` | idem | Parcial |
| `shared.agent_observability.persistence.tenant_billing_config_repository` | módulo `application/services/billing/` o similar | NO documentado |
| `shared.agent_observability.persistence.base_trace_event_repo` + `base_llm_call_repo` | repos sales_agent | NO documentado en skill (en SKILL.md "SSoT vivos" cita tablas pero no la abstracción shared) |
| `shared.agent_observability.channels.format_for_channel` | `OutputManager.process_response` | Sí (SKILL.md anti-pattern "Hardcodear canales literales en `OutputManager`. Usar `get_channel_format(channel_type)`") |
| `shared.agent_observability.channels.intent_detector` | probable consumer en routing/specialist | NO documentado |
| `shared.agent_observability.recording.sanitization::sanitize_payload` | callbacks + repos sales_agent | Sí (SKILL.md anti-pattern "Bypass `sanitize_payload`") |
| `shared.billing` (BudgetGuard + RateLimiter) | `OutputManager`/specialists (per SKILL.md "Budget + Outbound Gating") | Sí (SKILL.md sección dedicada) |
| `shared.compliance` (ComplianceService) | probable consumer | NO documentado |
| `shared.domain_events.outbox` | event emission sales_agent | Parcial (SKILL.md anti-pattern menciona `USE_OUTBOX_PATTERN_*`) |

**Acción dev-team:** ejecutar `grep -rn "from src.shared.agent_observability" backend/src/modules/sales_agent/ | grep -v __pycache__` + `grep -rn "from shared.agent_observability" backend/src/modules/sales_agent/` (cubrir ambas formas import) + `grep -rn "from src.shared.billing\|from src.shared.compliance" backend/src/modules/sales_agent/`. Output completo va a `T-1-impl-log.md::Surfaces compartidas (raw scan output)` antes de redactar la sección final del skill.

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Audit detecta que el módulo `sales_agent` viola anti-patterns documentados (e.g., mirror real de turn_envelope) | high | Documentar finding en `T-1-impl-log.md::Surface drift` + escalar Chris. NO refactorizar en esta story (out-of-scope). Crear story de refactor si requerido. |
| Test pytest cita lista hardcoded de invariantes canónicas (scenario 4) que con el tiempo se vuelve incompleta | medium | Agregar test `test_invariants_list_completeness` que asserta ≥4 invariantes (mínimo del spec); incrementar lista cuando agreguemos invariantes nuevas (commit-by-commit). |
| Política híbrida de resolución del scenario 4 escala a Chris en pleno build → blocker | medium | Documentar resolución pendiente en `T-1-impl-log.md::Contradictions pending Chris ratification`; transition state developing→blocked si bloquea. /pm escala. |
| `T-1-impl-log.md::Claims removed (archived)` crece muy grande si Q4 produce muchos DELETEs | low | Aceptable — preservar data verbatim es prioridad explícita Q4. Si crece >5000 líneas, considerar mover a archivo separado `T-1-archived-content.md` referenciado desde impl-log (decisión defer al builder; documentar en impl-log la elección). |
| Magic comment `<!-- voseo-allowed -->` agregado a `humanization-rules.md` o `sales-agent-brand-voice.md` se vuelve excesivo | low | Solo agregar comment cuando archivo CITA voseo verbatim (ej. glosario). Si no hay glosario, no agregar comment. |

## Decisiones registradas

- **2026-05-06 19:45Z** — Skip /architect-be sub-spawn (BE inline). Razón: surface trivial (1 test file), sin DDD nuevo, sin migrations, sin services. Chris explícito en handoff prompt: "incluye sub-arq BE inline ya que es único surface".
- **2026-05-06 19:45Z** — `production_code: false` para T-1. Razón R23: aunque story refiere sales_agent, el trabajo del audit es doc-engineering + test pytest. Owner pool sonnet/qwen, Opus NO requerido.
- **2026-05-06 19:45Z** — Single ticket T-1 (no split). Razón: scope coherente (audit + test + impl-log son una unidad lógica), estimate 5-6h <8h cap por ticket, dependencies trivializadas (sin handoffs cross-stack).

## Próximo paso

Ready package cerrado tras producir 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml + checkpoint transition refined→ready. Conv 2 (autonomous build) puede arrancar — `/dev-team` toma T-1 vía pickup standard.
