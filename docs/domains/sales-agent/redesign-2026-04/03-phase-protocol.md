# 03 · Phase Protocol — 10 pasos obligatorios

> **Actualizado 2026-04-28**: agregado **Paso 11 — Code review final** (cohesión + acoplamiento + no-broken-callers + cleanup oportunista).

Este protocolo es **obligatorio** en TODA fase. La fase debe citarlo en su Paso 1.

---

## Paso 1 — Re-lectura de contexto (10-20 min)

Releer en este orden:

1. `docs/domains/sales-agent/redesign-2026-04/README.md`
2. `00-vision-and-objectives.md` — **§3 (lo que NO se toca)**
3. `01-master-plan.md` — DAG y dónde encaja
4. `02-architecture-target.md` — topología destino
5. `04-principles.md` — principios senior
6. `05-tech-debt-log.md` — deuda detectada que pueda afectar esta fase
7. `phases/S{N}-*.md` — fase actual
8. `learnings/S{N-1}-*.md` — aprendizajes previos (si existe)
9. `audit/sales-agent-current-state.md` — mapa de cohesión/acoplamiento (post-S00)
10. `CLAUDE.md` raíz + reglas que la fase mencione (`.claude/rules/*.md`)
11. Skim del código relevante (sin clavarse).

Si algo del plan ya no aplica por aprendizajes → flag, NO seguir ciego.

---

## Paso 2 — Research fresco (15-45 min)

> **Estamos en abril 2026.** Lo que sabíamos en marzo puede estar desactualizado.

Cada fase tiene sección **"Research mandate"** con queries específicas.

Ejecutar:
- **WebSearch**: mínimo 3 queries del mandate. Anotar fuentes (URL + autor + fecha).
- **Tessl tiles** (`tessl-context` skill): tiles relevantes (`tessl__langgraph`, `tessl__fastapi`, etc.). Si no hay y central → instalar.
- **WebFetch** docs oficiales si query identificó URLs nuevas.
- Si la fase usa librería pivot: **verificar última versión + changelog**.
- Para integraciones externas (Mercado Pago, Stripe, Google Calendar, Cal.com): verificar API docs vigentes.

Productos:
- Lista de fuentes consultadas (al `learnings/`).
- Confirmación o ajuste del enfoque inicial. Si research sugiere cambio → **plan se ajusta antes de codear**.

---

## Paso 3 — Plan ejecutable (TaskCreate)

Tasks granulares con TaskCreate. Cada task ≤4 horas. Marcar dependencias.

Plantilla:
- **Subject**: imperativo, concreto.
- **Description**: archivos a tocar, criterio de hecho.
- Status `in_progress` al arrancar, `completed` al cerrar quality gate del task.

---

## Paso 4 — Ejecución TDD

> Regla 13 CLAUDE.md: **tests primero**.

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
cd backend && .venv/bin/pytest tests/admin/ -x -q

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

Si **algo** falla → no se cierra.

---

## Paso 6 — Verificación funcional

- Endpoint manual con `curl` o Streamlit admin si la fase agrega API.
- Smoke browser (skill `chrome-devtools-verify`) si toca FE.
- Trace inspection: query `sales_agent_trace_event` post-S1 / `copilot_trace_event` si aplica.
- §3 sigue funcionando:
  - Closer Studio muestra conversaciones live (`/sales/studio/inbox`).
  - WS `/closer-studio` emite eventos.
  - Webhooks Telegram/WhatsApp/IG procesan.
  - Smart debounce buffer agrega mensajes fragmentados.
  - Follow-up engine corre y NO repite.
  - Frozen detection cierra sesiones inactivas.
  - **Post-S00**: `/sales/resumen` 404 (deprecated borrado), redirect `/sales` → `/sales/studio/inbox` funciona.

---

## Paso 7 — Tech debt log

Si durante la fase detectaste:
- Bug ajeno (no del scope)
- Pattern incorrecto que se repite
- Test frágil
- Hardcoded value que debería ser registry
- Cualquier cosa que mereciera issue

→ Agregar entrada en `05-tech-debt-log.md`:
- Fecha + fase detectora + descripción + path exacto + impacto + acción + razón

**Regla:** si fixeaste, validá con test reproductor. NO patches sin entender root cause.

---

## Paso 8 — Documento de aprendizajes

Crear `learnings/S{N}-{slug}.md` desde `learnings/_template.md`. Denso, accionable, sin filler.

---

## Paso 9 — Generar prompt para fase siguiente

Editar `prompts/S{N+1}-start.md` (existe template precargado, refinar):

- Referencia a `phases/S{N+1}-*.md`.
- Lista de docs que la próxima fase debe releer.
- Branch state esperado (`development` limpio, último commit hash).
- Hooks nuevos que S{N+1} necesita saber.
- Tech debt detectado que S{N+1} debería tener en radar.

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

## Paso 11 — Code review final (NUEVO 2026-04-28)

> **Pre-cierre obligatorio.** Senior dev pass para asegurar alta cohesión + bajo acoplamiento + no-broken-callers.

Antes del commit final:

### 11.1 Callers no rotos

- Para cada símbolo (función/clase/endpoint) que **modificaste** o **eliminaste**:
  - `grep -r "<symbol>"` para encontrar callers.
  - Verificar callers actualizados o no afectados.
  - Si hay caller obsoleto → fix o flag DEFERRED.
- Para cada **schema DB** modificado:
  - Verificar repos que leen esa tabla.
  - Verificar admin Streamlit pages que la consultan.
  - Verificar workers que la tocan.

### 11.2 Cohesión

- ¿Cada archivo tocado tiene UNA responsabilidad?
- ¿Lógica nueva está donde corresponde semánticamente o donde fue cómodo?
- ¿Hay funciones muertas tras el refactor?

### 11.3 Acoplamiento

- ¿Algún import nuevo cruza módulos sin pasar por `shared/links/` o port declarado?
- ¿La fase introdujo dependency entre dos módulos antes desacoplados?
- ¿Hay circular import latente?

### 11.4 Skill `simplify` (si toca código)

Invocar `simplify` skill sobre los archivos modificados:
- Detecta duplicación.
- Sugiere reuso.
- Flag if-elsif chains que deberían ser strategy/registry.

Aplicar fixes obvios. DEFERRED el resto.

### 11.5 Cleanup oportunista

Mientras tocás un archivo:
- Imports no usados → borrar.
- Type `any`/sin tipos → tipar (sólo en código tocado).
- Comentarios stale (`# TODO: remove after X`) que ya cumplieron → borrar.
- Strings spanish neutro: si toca el archivo y veo voseo → fixear ese archivo (no ampliar scope).

### 11.6 Tests del módulo afectado verdes

Re-correr `pytest tests/modules/{módulo_tocado}/ -x -q` antes de commit. Si rompió algo lateral → fix.

### 11.7 Admin Streamlit smoke

Si la fase toca tablas que admin lee:
- `cd backend && .venv/bin/pytest tests/admin/test_admin_smoke.py -x -q`
- Streamlit UI manual smoke: render del page afectado sin exception.

---

## Reglas anti-deriva (críticas)

1. **No agregar features no listadas en la fase.** Oportunidad descubierta → `learnings/` o `05-tech-debt-log.md`. NO al código.
2. **No tocar §3.** Si parece necesario → parar, preguntar.
3. **No alucinar.** Path/símbolo no seguro → leer archivo, no inventar.
4. **No skip research.** Aunque "creas saber" — abril 2026, siempre algo cambió.
5. **No cerrar sin los 11 puntos.**
6. **Tests del módulo afectado verdes** antes de cerrar.
7. **Spanish neutro LATAM** en user-facing (sin voseo, excepto voz de marca tenant configurada).
8. **No-broken-callers** (Paso 11.1) es bloqueante. Si rompiste caller → fix antes de commit, no después.
