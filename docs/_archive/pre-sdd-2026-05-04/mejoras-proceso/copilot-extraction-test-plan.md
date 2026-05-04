# Plan de pruebas — Copilot Unified Extraction Flow

> Ejecutable en nueva conversación. Cubre el diseño commiteado en `8d0a63d3`.
> SSoT del diseño: `docs/mejoras-proceso/copilot-extraction-unified-design.md`.
> Fecha base: 2026-04-23.

## Objetivo

Validar end-to-end que el flujo unificado de extracción funciona correctamente para los 13 escenarios críticos, sin regresión en guided manual ni en brand studio.

---

## Prerequisitos (correr ANTES de cualquier escenario)

### 1. Entorno levantado

```bash
cd /home/chris/AISALESHT
/dev-up
# Verifica: visionarias_brain_dev, visionarias_client_dev, visionarias_postgres, visionarias_admin_dev running
docker compose ps | grep -E "brain_dev|client_dev|postgres"
```

### 2. Migraciones al día

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic current"
# Expected: 060_offer_extraction_traces (head)
```

### 3. Branch + commit correcto

```bash
git log --oneline -3
# Expected: ff80ae16, cb057abf, 8d0a63d3 en topes
```

### 4. Tenant + user de prueba

Usar el tenant `1fd1562b-2101-410a-870c-dc2f7e27b355` (el de la traza original). Email login: `hola@alpacapurpura.lat`.

### 5. Offer de prueba

Crear una offer vacía (sin data en secciones) para poder validar fill from scratch. O usar `a96403b5-c1db-4b31-97aa-cb18d08ad9f9` (de la traza original) — resetear campos si hace falta:

```sql
-- Opcional, solo si querés reset completo del offer de prueba
UPDATE products SET
  headline_promise = NULL,
  primary_outcome = NULL,
  time_to_value = NULL,
  target_avatar_match = NULL
WHERE id = 'a96403b5-c1db-4b31-97aa-cb18d08ad9f9' AND tenant_id = '1fd1562b-2101-410a-870c-dc2f7e27b355';
```

### 6. Sample URL + doc listos

- URL pública con contenido real: `https://visionarias.lat/products/de-proposito-a-prosperidad`
- Doc sample (PDF o TXT) con brief de producto — tener a mano para escenarios 6, 9.

### 7. Skill `chrome-devtools-verify` disponible

Confirmar que existe `.claude/skills/chrome-devtools-verify/`. Se usa para reproducir escenarios en vivo en `dev-app.nicolify.com`.

### 8. Queries de observabilidad listas

```sql
-- Turns de una conversación
SELECT turn_id, event_type, name, status, duration_ms, created_at
FROM copilot_trace_event
WHERE conversation_id = :conv_id
ORDER BY created_at;

-- Tool calls con args
SELECT turn_id, name, data->'args' AS args, data->'output_preview' AS out
FROM copilot_trace_event
WHERE conversation_id = :conv_id AND event_type = 'tool_call';

-- Procedure state actual
SELECT jsonb_pretty(procedure_state) FROM copilot_conversations WHERE id = :conv_id;

-- Messages (cards + text)
SELECT jsonb_pretty(messages) FROM copilot_conversations WHERE id = :conv_id;
```

---

## Matriz de escenarios

| # | Escenario | Tipo | Gate crítico |
|---|---|---|---|
| 1 | Guided start offer vacío | Smoke | `start_guided_setup` ejecuta, state persiste |
| 2 | URL en guided offer vacío, scope=faltantes | **Bug original** | `extract_from_url` llamado, NO loop `extract_structured` |
| 3 | URL en guided, scope=cero | Variante | mode=initial pisa todo |
| 4 | URL en guided, scope=sección actual | Variante | scope=section, section=<current_block_id> |
| 5 | Doc en guided vacío | Variante | `extract_from_doc`, ARQ job |
| 6 | Guided manual puro (sin URL/doc) | Regresión | No hay `active_extraction_job`, flujo normal |
| 7 | URL mid-flow (manual progress previo) | UX mid-flow | default scope=faltantes, respeta data manual |
| 8 | Doc mid-flow (manual progress previo) | UX mid-flow | mismo pero con asset |
| 9 | Doble dispatch URL (user paste 2x) | Edge | Segundo dispatch rechazado o idempotente |
| 10 | Extract completion → guided resume | Post-job | `active_extraction_job` limpia, `pending_field_paths` recalcula |
| 11 | extract_structured paths inválidos | DX | Tool retorna `text` informativo (no string vacío) |
| 12 | Free-form URL sin guided | Fuera scope diseño | `extract_from_url` funciona igual, pills aparecen |
| 13 | Brand URL extraction (no regresión) | Regresión | Brand sigue funcionando como antes |

---

## Escenario 1 — Guided start offer vacío (smoke)

### Setup
- Offer nueva vacía o resetear `a96403b5-...` como en prereq 5.
- Conversación copilot nueva (clear).

### Acción
Mensaje al copilot: `Llama start_guided_setup con domain="offer" y entity_id="<offer_id>"`.

### Expected
- Trace: `turn_start` → `tool_call: start_guided_setup` (status=ok) → `turn_end`.
- DB: `procedure_state` contiene `guided.current_block_id = "identity"`, `completed_blocks = []`.
- UI: respuesta lista 4 campos identity (public_name, headline_promise, primary_outcome, time_to_value), pregunta por cuál empezar.
- NO hay `active_extraction_job` en state.

### Verificar
```sql
SELECT jsonb_pretty(procedure_state) FROM copilot_conversations WHERE id = :conv_id;
-- guided key present, active_extraction_job absent
```

---

## Escenario 2 — URL en guided offer vacío, scope=faltantes (BUG ORIGINAL)

### Setup
Repetir escenario 1 (guided activo en identity block).

### Acción
Enviar: `La información de mi producto se encuentra en: https://visionarias.lat/products/de-proposito-a-prosperidad`.

### Expected

**Turno A (user envía URL)**:
- Trace: `tool_call: clarify` con opciones scope (cero / faltantes / sección actual).
- UI: card clarify visible con 3 opciones.
- NO hay `tool_call: extract_structured` en este turno.

**Turno B (user elige "Completar faltantes")**:
- Trace: `tool_call: extract_from_url` con args `{module: "offer", url: "https://...", scope: "full", mode: "update", entity_id: "..."}`.
- Trace: 1 solo tool_call, NO hay loop de 8× `extract_structured`.
- Response: texto "Inicié el análisis, 1-2 min...".
- DB: `procedure_state.active_extraction_job = {job_id, module: "offer", source_kind: "url", scope: "full", mode: "update", paused_at_block: "identity", ...}`.

**Fase 2 (durante la extracción, user chatea)**:
- Si user envía otro mensaje casual, LLM debe responder en tono conversacional sin llamar `extract_structured` sobre offer.
- Banner "EXTRACCIÓN EN CURSO" visible en cada prompt render.

**Fase 3 (~1-2 min, worker termina)**:
- `copilot_events` o `copilot_conversations.messages` contiene nav pills (`✓ Identidad lista · N campos`) por cada sección completada.
- Al final: card `extraction_summary` con coverage_by_section.
- DB: `procedure_state.active_extraction_job` ausente (limpiado por `handle_job_completed`).

**Turno C (user envía siguiente mensaje post-extracción)**:
- Prompt inyecta `pending_field_paths` con subset de identity fields aún vacíos (si hay).
- LLM pregunta solo por los vacíos, no por los llenos.

### Verificar
```sql
-- Turno A: solo clarify
SELECT name, data->'args' FROM copilot_trace_event
WHERE conversation_id = :conv_id AND event_type = 'tool_call'
ORDER BY created_at;
-- Expected: 1 row "clarify"

-- Turno B: solo extract_from_url
-- Expected: 1 row "extract_from_url" (NO 8× extract_structured)

-- Post-dispatch state
SELECT procedure_state->'active_extraction_job' FROM copilot_conversations WHERE id = :conv_id;
-- Expected: JSON con job_id, module=offer, paused_at_block=identity

-- Fase 3: cards
SELECT jsonb_array_elements(messages)->'blocks' FROM copilot_conversations WHERE id = :conv_id;
-- Expected: navigation cards + 1 extraction_summary card

-- Post-completion state
SELECT procedure_state->'active_extraction_job' FROM copilot_conversations WHERE id = :conv_id;
-- Expected: NULL (cleared)
```

### Criterio de éxito
Zero loops de `extract_structured`. Extracción real ocurre. Data poblada en offer. Nav pills visibles.

---

## Escenario 3 — URL en guided, scope=cero (mode=initial)

### Setup
Offer con algunos campos llenos manualmente.

### Acción
Pasar URL, elegir "Empezar desde cero".

### Expected
- `extract_from_url` con `mode="initial"`.
- Worker sobrescribe todos los campos, incluyendo los llenos.
- Summary card muestra total_fields alto.

### Verificar
```sql
SELECT name, data->'args'->>'mode' AS mode FROM copilot_trace_event
WHERE conversation_id = :conv_id AND name = 'extract_from_url';
-- Expected: "initial"
```

---

## Escenario 4 — URL en guided, scope=sección actual

### Setup
Offer en guided, bloque activo `identity`.

### Acción
Pasar URL, elegir "Solo sección actual".

### Expected
- `extract_from_url` con `scope="section"`, `section="identity"`.
- Worker actualiza solo identity, otras secciones intactas.

### Verificar
```sql
SELECT data->'args' FROM copilot_trace_event
WHERE name = 'extract_from_url' AND conversation_id = :conv_id;
-- Expected: {scope: "section", section: "identity", mode: "update"}
```

---

## Escenario 5 — Doc en guided vacío

### Setup
Offer vacío, guided activo. Subir un doc (PDF/TXT con brief).

### Acción
Adjuntar archivo + mensaje corto "procesá este brief".

### Expected
- Clarify scope (mismo patrón que URL).
- `tool_call: extract_from_doc` con `asset_id`, `module="offer"`.
- `procedure_state.active_extraction_job.source_kind = "doc"`.
- Preview_update events durante sync extraction.
- Summary card al terminar.

### Verificar
Similar a escenario 2 pero con `source_kind="doc"`.

---

## Escenario 6 — Guided manual puro (regresión)

### Setup
Offer vacío, guided activo, SIN URL ni doc.

### Acción
User responde campo por campo manualmente: "mi oferta se llama X", "la promesa es Y", etc.

### Expected
- Por cada turn con data: `tool_call: extract_structured` con field_path del campo respondido.
- NO `extract_from_url` ni `extract_from_doc`.
- `active_extraction_job` NUNCA aparece en state.
- `pending_field_paths` se reduce turn a turn.
- Al llegar a cobertura alta: `tool_call: advance_guided_block`.

### Verificar
```sql
SELECT procedure_state FROM copilot_conversations WHERE id = :conv_id;
-- active_extraction_job siempre absent, guided avanza blocks
```

### Criterio de éxito
Flujo guided clásico sigue igual. Zero regresión.

---

## Escenario 7 — URL mid-flow (manual progress previo)

### Setup
Offer con ~3 campos identity llenos manualmente. Guided en bloque `strategy`.

### Acción
Pasar URL.

### Expected
- Clarify con **default recomendado "Completar faltantes"** (porque hay progreso previo).
- User elige default.
- `extract_from_url` con `mode="update"`.
- `paused_at_block="strategy"` en active_extraction_job.
- Post-extracción: guided resume en `strategy` con `pending_field_paths` recalculado.

### Verificar
Message del LLM en clarify debe reconocer progreso: frase tipo "veo que ya avanzaste Identidad, voy a procesar respetando eso".

---

## Escenario 8 — Doc mid-flow

### Setup
Igual que escenario 7 pero con archivo adjunto en vez de URL.

### Expected
Mismo que 7 con `source_kind="doc"`.

---

## Escenario 9 — Doble dispatch URL (race)

### Setup
Guided activo, URL en vuelo (escenario 2 paso 3, pre-completion).

### Acción
User envía otra URL en Fase 2.

### Expected (por regla del prompt)
- LLM NO debe llamar `extract_from_url` segunda vez (regla #2 de guided.j2 active-extraction block).
- Respuesta al user: "ya hay un análisis en vuelo, espera que termine".

### Verificar
```sql
SELECT COUNT(*) FROM copilot_trace_event
WHERE conversation_id = :conv_id AND name = 'extract_from_url';
-- Expected: 1 (no se duplicó)
```

### Nota
Este es un soft enforcement (prompt-level). Si LLM ignora la regla, hay vector de race real — sería hallazgo para Item tech-debt futuro (rate-limit server-side).

---

## Escenario 10 — Extract completion → guided resume

### Setup
Post-escenario 2 (extracción terminó).

### Acción
User envía "¿qué falta?" o similar.

### Expected
- Prompt inyecta `pending_field_paths` = subset del bloque actual aún vacío (post-extracción).
- LLM responde listando solo lo pendiente, NO campos ya llenos por la extracción.
- Si bloque completo post-extracción: LLM sugiere `advance_guided_block`.

### Verificar
Respuesta del LLM no debe mencionar campos que ya tienen valor en DB.

---

## Escenario 11 — extract_structured paths inválidos (fix loop)

### Setup
Guided activo. Forzar LLM a llamar `extract_structured` con path inválido (vía mensaje tipo "guarda el campo foo_bar_fake con valor X").

### Expected
- Tool retorna JSON con `text` informativo: "Ninguno de los field_paths propuestos es válido en el dominio 'offer': `foo_bar_fake`. Revisa el catálogo editable y reintenta con paths existentes...".
- LLM recibe el text y NO retry mismo path inválido (corta loop).

### Verificar
```sql
SELECT data->'output_preview' FROM copilot_trace_event
WHERE conversation_id = :conv_id AND name = 'extract_structured'
ORDER BY created_at DESC LIMIT 1;
-- Expected: JSON con "text" no vacío explicando skip
```

---

## Escenario 12 — Free-form URL sin guided

### Setup
Conversación nueva. SIN `start_guided_setup`.

### Acción
Mensaje: `extrae de https://visionarias.lat/... hacia mi oferta abc-123`.

### Expected
- `extract_from_url` se llama igual (extraction toolset siempre disponible).
- `procedure_state.active_extraction_job` se escribe pero `paused_at_block=None`.
- Nav pills + summary card aparecen como siempre.
- Ningún layer "guided" ni "active extraction" visible en prompt (porque `guided_state=None`).

### Nota
Este caso NO valida el gap del Item 4 del tech-debt plan (pending_field_paths en free-form). Solo que URL extraction funciona sin guided.

---

## Escenario 13 — Brand URL extraction (no regresión)

### Setup
Conversación copilot, ruta `/brand-studio/identity`.

### Acción
`extrae de https://visionarias.lat hacia mi brand`.

### Expected
- Flujo idéntico al pre-commit: clarify scope + mode → `extract_from_url` module=brand.
- Nav pills + summary card brand igual que antes.
- `procedure_state.active_extraction_job` con `module="brand"`.

### Verificar
Compare trace con conversación previa exitosa brand (si existe).

---

## Cross-cutting checks (correr al final de cada sesión de testing)

### CC1 — Zero loops de tool repetidos
```sql
SELECT conversation_id, turn_id, name, COUNT(*) AS n
FROM copilot_trace_event
WHERE event_type = 'tool_call' AND created_at > now() - interval '1 hour'
GROUP BY conversation_id, turn_id, name
HAVING COUNT(*) > 3;
-- Expected: 0 rows (ningún tool llamado >3 veces en mismo turn)
```

### CC2 — Cards emitidas post-extracción
```sql
SELECT conversation_id, COUNT(*) AS pills
FROM copilot_trace_event
WHERE event_type = 'card_emitted' AND name = 'navigation'
  AND created_at > now() - interval '1 hour';
-- Expected: >= N secciones completadas por los escenarios corridos
```

### CC3 — active_extraction_job se limpia
```sql
SELECT id, procedure_state->'active_extraction_job' AS active
FROM copilot_conversations
WHERE tenant_id = :tenant AND updated_at > now() - interval '1 hour';
-- Expected: todos los rows con active = null (salvo los que tienen job in-flight activo)
```

### CC4 — Spanish neutro sin voseo
Revisar respuestas del LLM en los escenarios. No debe aparecer: `mirá`, `sabés`, `tenés`, `dale`, `andá`, `podés`. Sí: `mira`, `sabes`, `tienes`, `puedes`.

### CC5 — Tenant isolation
```sql
SELECT DISTINCT tenant_id FROM copilot_conversations
WHERE id IN (<conv_ids_de_la_sesión>);
-- Expected: single tenant_id
```

---

## Método de ejecución recomendado

### Opción A — Browser live (preferida, alta fidelidad)

1. Skill `chrome-devtools-verify` abre `dev-app.nicolify.com` en Chrome.
2. Login como `hola@alpacapurpura.lat`.
3. Navegar a offer editor: `/<tenant>/offer-studio/offer/<offer_id>/editor/identity`.
4. Abrir copilot panel.
5. Ejecutar cada escenario secuencialmente, anotando:
   - turn_id de cada turn (ver trazas)
   - observaciones UI (cards visibles, texto del LLM)
   - DB snapshot relevante
6. Screenshot cada escenario crítico.

### Opción B — Pytest integration tests (cobertura deterministica)

Complemento, no reemplazo. Para escenarios 1, 6, 11, 12, 13 que no requieren LLM real.

### Opción C — DB-only traza retrospectiva

Si un escenario ya ocurrió (ej. el bug original en conv `376850f5-...`), comparar trazas pre/post commit para validar que el fix cambió comportamiento.

---

## Reporte de resultados

Crear `docs/mejoras-proceso/reviews/copilot-extraction-test-results-<fecha>.md` con tabla:

| # | Escenario | Status | Evidencia | Notas |
|---|---|---|---|---|
| 1 | Guided start | ✅ PASS | turn_id xxx | - |
| 2 | URL guided faltantes | ✅ PASS | turn_ids xxx,yyy | Resolvió bug original |
| ... | ... | ... | ... | ... |

Status values: `PASS`, `FAIL`, `BLOCKED`, `SKIP`.

Por cada `FAIL`: abrir issue/task con reproducible steps + DB state.

---

## Criterio de done global

- 13/13 escenarios ejecutados.
- Escenarios 2, 6, 11 deben ser PASS (bug original + regresión guided + fix loop).
- Zero CRITICAL fallos en CC1-CC5.
- Reporte commiteado.

Si 2/13 fallan pero no son los críticos, se considera PASS parcial con issue follow-up.
