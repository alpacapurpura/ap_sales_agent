# 05-guidelines.md — Story maintenance-skill-sales-agent-audit

> Owner: `/architect`. Patterns concretos que `/dev-team` debe seguir/evitar. SIN AMBIGÜEDAD.

## Workflow del audit (4 pasadas — orden estricto)

El builder ejecuta el audit en estas 4 pasadas. NO improvisar el orden — cada pasada usa output de la anterior.

### Pasada 1 — Verificación mecánica (paths citados existen)

```bash
# Paths absolutos (ajustar):
SKILL_DIR=/home/chris/AISALESHT/.claude/skills/sales-agent-expert
REPO=/home/chris/AISALESHT

# Listar todos los símbolos/paths citados en SKILL.md + references/
# Patrón: regex para capturar `backend/src/...`, `modules/{m}/...`, `shared/{...}`,
#         class FooBar, table_name_examples, archivo.py, etc.
# Ver test fixture en backend/tests/scripts/test_skill_sales_agent_audit.py para regex final.

# Para cada match, intentar resolver:
#   - Si es path: Path("$REPO/$path").exists()
#   - Si es class/función: grep -rn "class Name\|def name(" backend/src/
#   - Si es tabla DB: grep -rn "Name\b" backend/alembic/versions/ + ORM models

# Output: tabla mental con (símbolo, path_citado, resuelve?, razón_no_resuelve)
```

**Output esperado pasada 1:** lista de paths/clases que no resuelven. Para cada uno:
- Si fue renombrado/movido → UPDATE: actualizar al path canónico
- Si fue eliminado pero relevante histórico → marcar línea con `OBSOLETO: <razón> — <reemplazo>`
- Si fue eliminado y irrelevante → DELETE (preservar verbatim en `T-1-impl-log.md::Claims removed (archived)`)

### Pasada 2 — Surfaces compartidas (consumers shared/agent_observability)

```bash
# AST scan: imports desde modules/sales_agent/ a shared/
grep -rn "from src.shared.agent_observability\|from shared.agent_observability" \
  $REPO/backend/src/modules/sales_agent/ 2>/dev/null | grep -v __pycache__

# Captura adicional para shared.billing y shared.compliance:
grep -rn "from src.shared.billing\|from shared.billing\|from src.shared.compliance\|from shared.compliance" \
  $REPO/backend/src/modules/sales_agent/ 2>/dev/null | grep -v __pycache__

# Para cada hit: extraer (subsystem, archivo cliente sales_agent)
# Compilar lista deduplicada
```

**Output esperado pasada 2:** lista bullets formato `- shared.agent_observability.{subsystem} → consumed by modules/sales_agent/{file}` para cada subsystem importado. Esta lista va a la **sección NEW** del skill `## Surfaces compartidas con copilot`. Ubicación de la sección: en SKILL.md, entre la sección "Decisiones cross-fase no obvias" y la sección "SSoT vivos".

### Pasada 3 — Decisiones cardinales últimos 60 días (3 fuentes)

```bash
# Fuente (a) — learnings.md últimos 60d
grep -E "^## 2026-0[3-5]" $REPO/docs/process/learnings.md | head -50

# Fuente (b) — git log 60d sobre módulos relevantes
git log --since="60 days ago" --oneline --no-merges \
  $REPO/backend/src/modules/sales_agent/ \
  $REPO/backend/src/shared/agent_observability/ 2>/dev/null

# Fuente (c) — stories archivadas con module:sales_agent
grep -lE "^module:\s*sales_agent" $REPO/docs/archive/2026/stories/**/*.md 2>/dev/null
# Lista las stories shipped recientes
```

**Output esperado pasada 3:** lista bullets formato `- YYYY-MM-DD — {decisión} ({source: learnings.md | commit short_hash | story id})`. Deduplicar (una decisión puede aparecer en 2+ fuentes — citar la fuente más autoritativa). Esta lista va a la **sección NEW** del skill `## Decisiones cardinales últimos 60 días`. Ubicación: justo después de `## Surfaces compartidas con copilot`.

**Decisiones esperadas mínimas (sanity check):**
- 2026-05-06 — `sales-agent-eval-runner-foundation` shipped → eval suite path establecido
- 2026-05-06 — `sales-agent-litellm-canonicalization` shipped → LiteLLM canonical path
- 2026-05-06 — Reframe synthetic-first PI-12 sales-agent-eval-foundation
- (otras detectadas durante el scan)

### Pasada 4 — Utility verdict por sección (KEEP|UPDATE|DELETE|RESTRUCTURE)

Para CADA sección H2/H3 de `SKILL.md` y CADA archivo `references/*.md` (4 archivos), emitir verdict explícito con razón citable. **No hay shortcut — recorrer linealmente.**

| Verdict | Cuándo aplicar | Acción |
|---|---|---|
| `KEEP` | Sección útil, vigente, refleja realidad código vivo | Sin cambio |
| `UPDATE` | Sección útil pero contiene paths/claims stale | Modificar in-place; documentar diff en `T-1-impl-log.md::Claims updated` con before/after |
| `DELETE` | Sección obsoleta, irrelevante post-cambio reciente, sin reemplazo necesario | Eliminar de archivo; preservar verbatim en `T-1-impl-log.md::Claims removed (archived)` con razón |
| `RESTRUCTURE` | Contenido útil pero mal organizado / fragmentado / debe moverse a otra sección o archivo | Reorganizar; preservar versión pre-cambio en `T-1-impl-log.md::Claims removed (archived)` + entrada en `Claims added` con nueva ubicación |

**Output esperado pasada 4:** tabla `### Utility verdicts` en `T-1-impl-log.md` con formato:

```markdown
### Utility verdicts

| Sección/Archivo | Verdict | Razón |
|---|---|---|
| SKILL.md `## §0 — Anti-duplication cardinal` | KEEP | Refleja realidad post PR-1 PI-1.1 hotfix; inventario shared válido. |
| SKILL.md `## §3 — NO se toca` | UPDATE | Línea 38 cita `agent_state_checkpoint` schema; verificar paths/columnas vigentes. |
| SKILL.md `## Budget + Outbound Gating (PI-1 S0 PR-2)` | UPDATE | Referencia a CONTRACT.md archivado en docs/archive/2026/legacy-pis/...; actualizar pointer y/o marcar OBSOLETO. |
| SKILL.md `## Pointers` línea 122-125 | UPDATE | Verificar paths citados en docs/domains/sales-agent/redesign-2026-04/ existen. |
| references/sales-agent-brand-voice.md (todo) | KEEP | Recientemente actualizado 2026-05-04, refleja compiler v2. |
| references/humanization-rules.md (todo) | UPDATE | Sin updates desde 30-marzo; verificar paths + magic comment voseo-allowed. |
| references/conversation-stages.md (todo) | KEEP | Stages enum actuales (verificar grep), sin cambios módulo recientes que contradigan. |
| references/tool-patterns.md (todo) | UPDATE | Verificar tools listados existen en `application/tools/registry.py`. |
| ... | ... | ... |
```

100% cobertura — cada H2 + H3 de SKILL.md + cada archivo de references debe tener entry. Test `test_utility_verdicts_cover_all_skill_sections` asserta esto.

## Patterns required

- TDD strict (R8): escribir el test pytest primero (RED), después aplicar diff al skill hasta GREEN
- Test parsea skill via `re` + `pathlib` puro — sin librerías exóticas (markdown parser, etc.). Precedente: `backend/tests/scripts/test_pre_commit_hook.py`
- Test idempotente: pure filesystem reads, sin DB/network/LLM
- Imports `from __future__ import annotations` + `from pathlib import Path` + `import re` + `import ast` (para AST scan de imports python)
- Constants top-level resueltos via `Path(__file__).resolve().parents[3]` para encontrar REPO_ROOT (precedente test_pre_commit_hook.py línea 23)
- Marker `OBSOLETO:` con prefix mayúsculas + `:` + razón post-marker. Regex referencia: `^OBSOLETO:\s*(.+?)\s*[—:→]\s*(.+)$`
- Magic comment `<!-- voseo-allowed -->` agregado a `references/humanization-rules.md` y/o `references/sales-agent-brand-voice.md` SOLO si dichos archivos contienen voseo verbatim (verificar con grep voseo glosario antes de agregar)
- Política híbrida resolución (scenario 4):
  - Auto-resolve si contradicción es entre `SKILL.md` y `references/*.md` del mismo skill (gana SKILL.md, ajustar reference)
  - Escalar Chris si contradicción es vs `.claude/rules/*.md` externo, vs otro skill (`copilot-expert`), o entre 2 references sin árbitro en SKILL.md
- Preservación data: TODA línea/sección eliminada por DELETE/RESTRUCTURE va verbatim a `T-1-impl-log.md::Claims removed (archived)` con metadata (archivo origen + sección + razón eliminación)
- Spanish neutro en frases nuevas (excepto cuando cita output del agente, que respeta voz tenant — voseo OK ahí)
- Stage commits por nombre exacto (`git add docs/product/stories/.../01-spec.md` etc.) — prohibido `git add -A`
- Conventional commits: `chore(skill): audit sales-agent-expert + verify paths against live code (T-1)`

## Patterns forbidden

- ❌ Crear nuevos archivos en `references/` (estructura del skill se preserva — AD2)
- ❌ Mergear o splittear archivos existentes de `references/` (idem)
- ❌ Borrar contenido sin preservar verbatim en `T-1-impl-log.md::Claims removed (archived)` (cero pérdida de data — Q4)
- ❌ Crear nuevos archivos en `backend/src/modules/sales_agent/` o `backend/src/shared/` (story es doc-only)
- ❌ Crear migrations
- ❌ Crear nuevas reglas en `.claude/rules/` (out-of-scope; si el audit detecta need de nueva rule, escalar Chris)
- ❌ Modificar `copilot-expert` skill o cualquier otro skill (out-of-scope)
- ❌ Cambiar la estructura del frontmatter de SKILL.md (`name:`, `description:`) — content only
- ❌ Tocar `personality_profiles.system_instruction` invariante o cualquier SSoT viva del módulo
- ❌ Refactorizar el módulo `sales_agent` aunque el audit detecte anti-pattern (out-of-scope; escalar Chris para crear story de refactor)
- ❌ Saltarse alguna de las 4 pasadas (orden estricto — cada pasada usa output de la anterior)
- ❌ Auto-resolver contradicción cross-skill o vs rules externas (debe escalar Chris)
- ❌ Reportar GREEN sin haber generado `T-1-impl-log.md` con las 4 secciones obligatorias
- ❌ Usar test markers `xfail` o `skip` para "pasar" CI — corregir la causa
- ❌ `// TODO`, `# TODO`, `# HACK`, `// FIXME` en código del test (cero deuda técnica — esta misma story es de cero deuda técnica documental, mismo standard aplica al test)

## Files in scope (dev-team edita SOLO estos)

- `backend/tests/scripts/test_skill_sales_agent_audit.py` (NEW — el test de regresión)
- `.claude/skills/sales-agent-expert/SKILL.md` (modify — agregar 2 secciones nuevas, marcar OBSOLETO, aplicar UPDATE/DELETE/RESTRUCTURE per verdicts)
- `.claude/skills/sales-agent-expert/references/conversation-stages.md` (modify per verdicts)
- `.claude/skills/sales-agent-expert/references/humanization-rules.md` (modify per verdicts; magic comment voseo-allowed si aplica)
- `.claude/skills/sales-agent-expert/references/sales-agent-brand-voice.md` (modify per verdicts; magic comment voseo-allowed si aplica)
- `.claude/skills/sales-agent-expert/references/tool-patterns.md` (modify per verdicts)
- `docs/product/stories/maintenance-skill-sales-agent-audit/T-1-impl-log.md` (NEW — log del audit con 4 H3 obligatorios)
- `docs/product/stories/maintenance-skill-sales-agent-audit/T-1-result.md` (NEW — handoff final del ticket; opcional si /dev-team lo requiere)
- `docs/product/stories/maintenance-skill-sales-agent-audit/checkpoint.md` (modify — state transitions developing → developed al cierre del ticket)

## Files dev-team NEVER touches (escalate to Chris)

- `backend/src/modules/sales_agent/**` (cero runtime impact)
- `backend/src/shared/agent_observability/**` (cero runtime impact)
- `backend/src/shared/billing/**` o `backend/src/shared/compliance/**` (idem)
- `backend/alembic/versions/**` (no migrations)
- `frontend/src/**` (no FE)
- `frontend/e2e/**` (no E2E)
- Otros skills en `.claude/skills/` (`copilot-expert/`, etc.)
- Otras rules en `.claude/rules/`
- `docs/process/learnings.md` (solo `/pm` lo edita)
- `docs/product/BACKLOG.md` (auto-gen — solo `/pm`)
- `MEMORY.md` (solo `/pm`)
- Outcomes/`pi-12-sales-agent-eval-foundation.md` (solo `/pm`)
- Otras stories en `docs/product/stories/` que no sean esta

## Reference docs (load before coding)

- skill `sales-agent-expert` mismo (es el TARGET del audit — leerlo entero antes de empezar)
- `.claude/rules/anti-duplication.md` (inventario shared abstractions — referenciado por el skill, validar coherencia)
- `.claude/rules/spanish-text.md` (voseo glosario + magic comment regex)
- `.claude/rules/parallel-safety.md` (M1-M8 — esp. M8 archivos del skill durante audit)
- `.claude/rules/git-safety.md` (stage por nombre)
- `.claude/rules/tdd-mandatory.md` (RED → GREEN → REFACTOR)
- `01-spec.md` de esta story (4 scenarios + decisions Q1-Q5 + NFR)
- `03-arch.md` de esta story (test design detallado AD1-AD6)
- `backend/tests/scripts/test_pre_commit_hook.py` (precedente — test pattern sobre artefactos no-runtime)
- `backend/tests/scripts/conftest.py` (fixtures comunes si dev-team los necesita)

## Validation antes de cerrar ticket

Antes de marcar T-1 como `developed`, dev-team verifica:

- [ ] `backend/tests/scripts/test_skill_sales_agent_audit.py` existe + pasa GREEN
- [ ] Cada validator de `04-validators.yaml::scenario_coverage` corre y retorna `must_pass:true`
- [ ] `T-1-impl-log.md` tiene los 4 H3 obligatorios poblados (`Claims removed (archived)`, `Claims updated`, `Claims added`, `Utility verdicts`)
- [ ] Tabla `Utility verdicts` cubre 100% de secciones H2/H3 + 100% de references files
- [ ] `git diff --name-only HEAD~N..HEAD -- backend/src/ frontend/src/ | wc -l` = 0
- [ ] Pre-commit hook pasa con archivos staged (no voseo en líneas user-facing nuevas)
- [ ] `make ci-parity` corrió GREEN si dev-team modificó algo no-trivial

## Handoff downstream

Una vez T-1 cerrado y story state=`developed`:

- `/auditor` (Chris triggers manualmente Conv 3) lee `01-spec.md` + `03-arch.md` + `T-1-impl-log.md` + diff
- Verifica los 4 scenarios cubiertos, política híbrida aplicada, preservación data verbatim, magic comment voseo-allowed correcto
- APPROVED → `/pm` aplica merge → capability promotion N/A (story es maintenance, no introduce capability nueva) → archive a `docs/archive/2026/stories/maintenance-skill-sales-agent-audit/`
- Stories downstream que esperaban este audit (`eval-foundation-tenant-seed-data`, `eval-foundation-simulator-homologation`, etc.) ahora pueden arrancar refining → refined → ready con confianza en el skill SSoT
