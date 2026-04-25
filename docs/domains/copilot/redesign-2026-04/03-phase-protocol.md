# Protocolo obligatorio por fase

Toda fase del plan sigue este protocolo. Las fases lo **deben citar** en su primer paso.

---

## Paso 1 — Re-lectura de contexto (10-15 min)

Antes de tocar código, releer en este orden:

1. `docs/domains/copilot/redesign-2026-04/README.md`
2. `docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md` — **prestar atención a §3 (lo que NO se toca)**.
3. `docs/domains/copilot/redesign-2026-04/01-master-plan.md` — DAG completo + dónde encaja esta fase.
4. `docs/domains/copilot/redesign-2026-04/02-architecture-target.md` — topología destino.
5. `docs/domains/copilot/redesign-2026-04/phases/F#-*.md` — la fase actual.
6. `docs/domains/copilot/redesign-2026-04/learnings/F{#-1}-*.md` — aprendizajes de la fase previa (si existe).
7. CLAUDE.md raíz + `.claude/rules/copilot-resilience.md` + reglas que la fase mencione.
8. Skim del estado actual del código relevante (sin clavarse en detalle).

Si algo del plan ya no aplica por aprendizajes previos → flagearlo, NO seguir ciego.

---

## Paso 2 — Pasada de research fresco (15-30 min)

> **Estamos en abril 2026.** Lo que sabíamos en marzo puede estar desactualizado.

Cada fase tiene en su doc una sección **"Research mandate"** con queries específicas.

Hacer:

- **Web search** con WebSearch tool. Mínimo 2-3 queries del mandate. Anotar fuentes.
- **Tessl tiles** (skill `tessl-context`) — buscar tiles relevantes (ej. `tessl__langgraph`, `tessl__fastapi`, `tessl__zod`). Si no hay tile y el tema es central, instalarlo.
- **WebFetch** docs oficiales si la query identificó URLs nuevas relevantes.
- Si la fase usa una librería (deepagents, trafilatura, etc.) — **siempre verificar versión más reciente y changelog**. No asumir.

Productos del paso 2:

- Lista de fuentes consultadas (irá al `learnings/`).
- Confirmación o ajuste del enfoque inicial. Si el research sugiere que la solución cambió, **el plan se ajusta antes de codear**.

---

## Paso 3 — Plan ejecutable (TaskCreate)

Crear tasks granulares con TaskCreate. Cada task ≤4 horas. Marcar dependencias.

Plantilla por task:

- **Subject**: imperativo, concreto.
- **Description**: archivos a tocar, criterio de hecho.
- Status `in_progress` cuando arranca, `completed` cuando pasa quality gate del task.

No hacer lista de 30 tasks. Mantener foco. Nuevos tasks aparecen al avanzar.

---

## Paso 4 — Ejecución TDD

> Regla 13 de CLAUDE.md: **tests primero**.

Por cada bloque de código nuevo:

1. Test que reproduce el comportamiento target → RED.
2. Implementación mínima → GREEN.
3. Refactor con tests verdes.

Para regresiones: test reproduce bug **antes** de fix.

Para arch invariants nuevos: agregar fitness test en `tests/architecture/`.

---

## Paso 5 — Quality gates (obligatorios antes de cerrar)

Native (nunca `docker exec`):

```bash
# Backend
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q

# Frontend (si la fase tocó FE)
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run
cd frontend && npx vitest run src/__tests__/architecture/
```

Migraciones (si aplica):

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"
# verificación en clone DB ver .claude/rules/backend-migrations.md
```

Si **algo** falla, no se cierra la fase. Se arregla o se revierte el bloque problemático.

---

## Paso 6 — Verificación funcional

- Endpoint manual con `curl` o Postman si la fase agrega API.
- Smoke browser (skill `chrome-devtools-verify`) si la fase toca FE.
- Trace inspection en admin Streamlit `/trazas` si la fase toca el copilot graph.
- Confirmar que **lo del §3 (no tocar) sigue funcionando**:
  - Audio dual-mode envía y reproduce.
  - History sidebar sigue paginando.
  - SSE v2 sigue emitiendo bloques.
  - Cards (proposal/clarify/preview_update/plan_card) renderean.

---

## Paso 7 — Documento de aprendizajes

Crear `learnings/F#-{slug}.md` siguiendo `learnings/_template.md`. Mínimo:

- **Resumen 3 líneas**: qué se entregó.
- **Decisiones clave**: lista breve, con razón.
- **Fuentes research**: links que consultaste con bullet de qué te aportó.
- **Sorpresas / gotchas**: lo que no esperabas. Si descubriste que la versión X de Y rompió algo, documenta.
- **Recomendaciones para fase siguiente**: ajustes al plan F{#+1} basados en lo aprendido.
- **Lo que NO funcionó / descarté**: dead branches que probaste y por qué se cayeron. Evita repetirlas.

---

## Paso 8 — Generar prompt para fase siguiente

Crear `prompts/F{#+1}-start.md` desde `prompts/_template.md`, completando:

- Referencia a `phases/F{#+1}-*.md`.
- Lista de docs que la próxima fase debe releer (incluyendo `learnings/F#-*.md`).
- Branch state esperado (`development` limpio, último commit hash).
- Cualquier hook nuevo que F{#+1} necesite saber por aprendizajes de F#.

---

## Paso 9 — Commit final + reporte

- Commit conventional con scope claro (ej. `feat(copilot-redesign-f1): provider pattern + discovery`).
- Cuerpo del commit menciona learning doc + prompt generado.
- Push a `development` (ver `.claude/rules/parallel-safety.md` — solo archivos de la sesión, nunca `git add -A`).
- Reportar al usuario:
  - Resumen 3 líneas de entregado.
  - Path al `learnings/F#-*.md`.
  - Path al `prompts/F{#+1}-start.md` listo para pegar.

---

## Reglas anti-deriva (críticas)

1. **No agregar features no listadas en la fase.** Si descubrís oportunidad → al `learnings/` como recomendación, NO al código.
2. **No tocar §3 (lo que NO se toca).** Si parece necesario → parar, preguntar al usuario.
3. **No alucinar.** Si no estás seguro de un path/símbolo → leer el archivo, no inventar.
4. **No skip research.** Aunque "creas saber" — abril 2026, siempre algo cambió.
5. **No cerrar fase sin los 7 puntos** de `00-vision-and-non-goals.md §4`.
6. **No tocar otros módulos sin que sigan funcionando.** Tests del módulo afectado verdes antes de cerrar.
