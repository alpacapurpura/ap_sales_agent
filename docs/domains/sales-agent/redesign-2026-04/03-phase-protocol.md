# 03 · Phase Protocol — 9 pasos obligatorios

Este protocolo es **obligatorio** en TODA fase. La fase debe citarlo en su Paso 1.

---

## Paso 1 — Re-lectura de contexto (10-20 min)

Releer en este orden:

1. `docs/domains/sales-agent/redesign-2026-04/README.md`
2. `docs/domains/sales-agent/redesign-2026-04/00-vision-and-objectives.md` — **§3 (lo que NO se toca)**
3. `docs/domains/sales-agent/redesign-2026-04/01-master-plan.md` — DAG y dónde encaja
4. `docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md` — topología destino
5. `docs/domains/sales-agent/redesign-2026-04/04-principles.md` — principios senior
6. `docs/domains/sales-agent/redesign-2026-04/05-tech-debt-log.md` — deuda detectada que pueda afectar esta fase
7. `docs/domains/sales-agent/redesign-2026-04/phases/S{N}-*.md` — fase actual
8. `docs/domains/sales-agent/redesign-2026-04/learnings/S{N-1}-*.md` — aprendizajes previos (si existe)
9. `CLAUDE.md` raíz + reglas que la fase mencione (`.claude/rules/*.md`)
10. Skim del código relevante (sin clavarse).

Si algo del plan ya no aplica por aprendizajes → flag, NO seguir ciego.

---

## Paso 2 — Research fresco (15-45 min)

> **Estamos en abril 2026.** Lo que sabíamos en marzo puede estar desactualizado.

Cada fase tiene sección **"Research mandate"** con queries específicas.

Ejecutar:
- **WebSearch**: mínimo 3 queries del mandate. Anotar fuentes (URL + autor + fecha).
- **Tessl tiles** (`tessl-context` skill): buscar tiles relevantes (`tessl__langgraph`, `tessl__fastapi`, `tessl__zod`, `tessl__tailwind`, etc.). Si no hay y el tema es central, instalar.
- **WebFetch** docs oficiales si la query identificó URLs nuevas.
- Si la fase usa librería pivot: **verificar última versión + changelog**. NO asumir.
- Para integraciones externas (Mercado Pago, Stripe, Google Calendar, Cal.com): verificar API docs vigentes — endpoints, auth, webhooks.

Productos:
- Lista de fuentes consultadas (al `learnings/`).
- Confirmación o ajuste del enfoque inicial. Si research sugiere cambio → **plan se ajusta antes de codear**.

---

## Paso 3 — Plan ejecutable (TaskCreate)

Crear tasks granulares con TaskCreate. Cada task ≤4 horas. Marcar dependencias.

Plantilla:
- **Subject**: imperativo, concreto.
- **Description**: archivos a tocar, criterio de hecho.
- Status `in_progress` al arrancar, `completed` al cerrar quality gate del task.

Mantener foco. No lista de 30 tasks. Nuevos tasks aparecen al avanzar.

---

## Paso 4 — Ejecución TDD

> Regla 13 CLAUDE.md: **tests primero**.

Por bloque de código nuevo:
1. Test que reproduce comportamiento target → RED.
2. Implementación mínima → GREEN.
3. Refactor con tests verdes.

Para regresiones: test reproduce bug **antes** de fix.

Para arch invariants nuevos: agregar fitness test en `tests/architecture/`.

---

## Paso 5 — Quality gates (obligatorios antes de cerrar)

Native (NUNCA `docker exec`):

```bash
# Backend
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest tests/modules/sales_agent/ -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q

# Frontend (si aplica)
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run
```

Migraciones:
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"
# Verificar idempotencia: re-correr → 0 cambios
# Test en clone DB ver .claude/rules/backend-migrations.md
```

Si **algo** falla → no se cierra. Se arregla o se revierte.

---

## Paso 6 — Verificación funcional

- Endpoint manual con `curl` o Streamlit admin si la fase agrega API.
- Smoke browser (skill `chrome-devtools-verify`) si toca FE.
- Trace inspection: query `sales_agent_trace_event` post-S1 / `copilot_trace_event` si aplica.
- §3 sigue funcionando:
  - Closer Studio muestra conversaciones live.
  - WS `/closer-studio` emite eventos.
  - Webhooks Telegram/WhatsApp/IG procesan correctamente.
  - Smart debounce buffer agrega mensajes fragmentados.
  - Follow-up engine corre y NO repite.
  - Frozen detection cierra sesiones inactivas.

---

## Paso 7 — Tech debt log

Si durante la fase detectaste:
- Bug ajeno (no del scope)
- Pattern incorrecto que se repite
- Test frágil
- Hardcoded value que debería ser registry
- Cualquier cosa que mereciera issue

→ Agregar entrada en `05-tech-debt-log.md` con:
- Fecha
- Fase que lo detectó
- Descripción + path exacto
- Impacto (CRITICAL / HIGH / MEDIUM / LOW)
- Acción tomada (FIXED / DEFERRED / FLAGGED) + razón
- Si DEFERRED: qué fase futura debería tomarlo

**Regla:** si fixeaste el tech debt, validalo con test reproductor. NO patches sin entender root cause.

---

## Paso 8 — Documento de aprendizajes

Crear `learnings/S{N}-{slug}.md` desde `learnings/_template.md`.

**Regla de oro:** lo va a leer la fase siguiente. Solo escribir lo que NECESITA saber. Si una sección no aplica → eliminarla. Doc corto y denso > largo y vacío.

Contenido mínimo:
- **Resumen 3 líneas**: qué se entregó, qué decisión no obvia se tomó, qué queda listo para la siguiente.
- **Decisiones clave**: solo donde el camino tomado no era el único razonable. Razón + alternativa descartada.
- **Sorpresas / gotchas críticos**: bugs de versión, comportamiento no documentado, fragility, discrepancia plan vs realidad.
- **Recomendaciones accionables para S{N+1}**: cada bullet = acción concreta.
- **Hooks listos**: paths exactos + cómo activarlos.
- **Riesgos abiertos**: qué puede romper + dónde mirar primero.
- **Fuentes research útiles**: solo las que cambiaron una decisión.

Anti-patrones:
- Listas exhaustivas de archivos modificados (ya está en `git diff`).
- Métricas inventadas si no se midieron.
- Repetir lo de `02-architecture-target.md`.
- Secciones con "N/A" o bullets vacíos.
- "Todo funcionó bien" sin contenido detrás.

Criterio de cierre: si S{N+1} sería igual de eficiente sin esta nota → sobra.

---

## Paso 9 — Generar prompt para fase siguiente

Editar `prompts/S{N+1}-start.md` (existe template precargado, refinar con contexto fresco):

- Referencia a `phases/S{N+1}-*.md`.
- Lista de docs que la próxima fase debe releer (incluyendo `learnings/S{N}-*.md`).
- Branch state esperado (`development` limpio, último commit hash).
- Hooks nuevos que S{N+1} necesita saber por aprendizajes de S{N}.
- Tech debt detectado en S{N} que S{N+1} debería tener en radar.

---

## Paso 10 — Commit final + reporte

- Commit conventional con scope claro (ej. `feat(sales-agent-redesign-s1): callback handler + dual-write`).
- Cuerpo del commit menciona learning doc + prompt generado.
- Push a `development` (ver `.claude/rules/parallel-safety.md` — solo archivos de la sesión, NUNCA `git add -A`).
- Reportar al usuario:
  - Resumen 3 líneas de entregado.
  - Path al `learnings/S{N}-*.md`.
  - Path al `prompts/S{N+1}-start.md` listo para pegar.

---

## Reglas anti-deriva (críticas)

1. **No agregar features no listadas en la fase.** Oportunidad descubierta → `learnings/` como recomendación o `05-tech-debt-log.md`. NO al código.
2. **No tocar §3.** Si parece necesario → parar, preguntar.
3. **No alucinar.** Path/símbolo no seguro → leer archivo, no inventar.
4. **No skip research.** Aunque "creas saber" — abril 2026, siempre algo cambió.
5. **No cerrar sin los 10 puntos** del Definition of Done de §4 de `00-vision-and-objectives.md`.
6. **Tests del módulo afectado verdes** antes de cerrar.
7. **Spanish neutro LATAM** en user-facing (sin voseo).
