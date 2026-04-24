# Plan de deuda técnica — post commit `8d0a63d3`

> Generado 2026-04-23 tras merge de "unified guided-aware extraction flow" en development.
> Ejecutable en una nueva conversación. Cada item es autónomo, tiene archivos concretos y criterios de done.

## Contexto

El commit `8d0a63d3` cerró el bug del loop de 8× `extract_structured` y trajo paridad arquitectónica offer↔brand en extracción. Quedaron 4 items de deuda conocida.

SSoT del diseño base: `docs/mejoras-proceso/copilot-extraction-unified-design.md`.

Arrancar en una nueva conversación leyendo este doc + el commit `8d0a63d3` para tener el contexto completo:

```bash
git show --stat 8d0a63d3
cat docs/mejoras-proceso/copilot-extraction-unified-design.md
cat docs/mejoras-proceso/tech-debt-plan-post-extraction-unified.md  # este archivo
```

---

## Item 1 — Audit review formal del commit

### Objetivo
Obtener `REVIEW.md` producido por `nicolify-backend-auditor` sobre el diff ya mergeado a `development`, para detectar findings que no vi en mi audit manual rápido.

### Scope
Solo los archivos del commit `8d0a63d3` (25 files). No auditar el resto del repo.

### Pasos

1. Arrancar el agente:
   ```
   Spawn nicolify-backend-auditor con prompt:
   - Audit commit 8d0a63d3 (full diff)
   - Leer docs/mejoras-proceso/copilot-extraction-unified-design.md primero
   - Focus: tenant isolation, DDD boundaries, SQLA 2.0, PII/response_model,
     migraciones idempotencia, Spanish neutro, best-effort failure handling,
     race conditions worker↔subscriber, coverage de tests
   - Output: docs/mejoras-proceso/reviews/8d0a63d3-extraction-unified.md
     con veredicto APPROVE / CHANGES_REQUIRED / BLOCK + findings citados
     file:line
   - NO modificar código, solo reporte
   ```

2. Leer el REVIEW.md producido.

3. Para cada finding CRITICAL o HIGH:
   - Crear task con descripción del fix
   - Aplicar cambio
   - Re-correr gates relevantes (ruff + pytest del módulo afectado)

4. Si auditor reporta CHANGES_REQUIRED, hacer commit follow-up:
   `fix(copilot|offer): resolve audit findings from REVIEW 8d0a63d3`

### Criterio de done
- REVIEW.md existe en `docs/mejoras-proceso/reviews/`
- Todos los findings CRITICAL/HIGH resueltos o justificados en comment inline
- Ruff + pytest modulo afectado pasan

### Estimación
30 min audit + 0-2h fixes según hallazgos.

---

## Item 2 — `test_streaming_timeout.py` falla en native WSL

### Objetivo
Test pasa igual en native WSL que en Docker (sin hardcodear hostname `postgres`).

### Síntoma
```
tests/modules/copilot/test_streaming_timeout.py::test_timeout_persists_partial_response FAILED
psycopg2.OperationalError: could not translate host name "postgres" to address: Temporary failure in name resolution
```

El test intenta abrir connection pool usando hostname `postgres` (resolvible en docker network, NO en WSL). El test no es mío pero bloquea `/test-backend` native, violando CLAUDE.md rule 2 "Native-First".

### Diagnóstico preliminar
El test usa `SessionLocal()` de `src.core.database`. `SessionLocal` lee `DATABASE_URL` del env. En dev-containers env apunta a `postgres:5432`; en WSL nativo debería apuntar a `localhost:5432` (o `127.0.0.1:5432`).

### Pasos

1. Reproducir:
   ```bash
   cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/modules/copilot/test_streaming_timeout.py -x -q --tb=long
   ```

2. Identificar el `DATABASE_URL` que usa el test. Opciones:
   - `.env` en repo root
   - `backend/.env`
   - Variables en shell
   - Default en `core/config.py`

3. Opciones de fix (elegir la menos invasiva):

   **a. Mock DB en el test** — si el test no necesita DB real, mockear `SessionLocal`.
   **b. Skip on WSL** — `@pytest.mark.skipif(os.getenv("CI") != "true" and not _postgres_reachable(), reason="...")`. Gross.
   **c. Fix env default** — si el test solo usa `.env` del repo, cambiar `postgres` → `localhost` en dev.
   **d. Docker compose mapping** — asegurar que postgres escucha 5432 en localhost desde WSL (ya debería estar — `docker compose.yml` port mapping).

4. Verificar:
   ```bash
   docker exec visionarias_postgres psql -U postgres -c "SELECT 1;"   # desde host
   docker exec visionarias_postgres bash -c "ss -tnlp | grep 5432"    # listener
   ```

5. Si es env: fix + documentar en `CLAUDE.md` o `backend/.env.example`.

6. Correr todo el módulo:
   ```bash
   .venv/bin/pytest tests/modules/copilot/ -q --timeout=60
   ```

### Criterio de done
- Test pasa en native WSL sin `@pytest.mark.skip`
- `/test-backend` no tiene test en rojo por este caso
- Si se cambió env, doc en CLAUDE.md o `.env.example`

### Estimación
30-60 min.

---

## Item 3 — Extraer base class `BaseExtractionOrchestrator` a `shared/`

### Objetivo
DRY entre `brand_extraction_orchestrator` y `offer_extraction_orchestrator`. Actualmente duplican lógica de waves, merge+save, announce, progress callback.

### Cuándo disparar
**No ahora.** Regla CLAUDE.md: "no premature abstraction". Disparar cuando aparezca el 3er módulo con extracción (landing, persona, asset). Si el 3er caso aparece o se planifica, entonces hacer este item.

### Scope propuesto (cuando toque)

**Crear**: `backend/src/shared/application/extraction/base_orchestrator.py`

```python
class BaseExtractionOrchestrator(Generic[TService, TEntity, TSettings]):
    """Abstract wave-based extraction orchestrator.

    Hooks (overridden by subclasses):
    - define_waves() -> list[list[str]]  # section slugs per wave
    - extract_section(section, content, ctx) -> SectionUpdate
    - merge_settings(current, updates) -> TSettings
    - save_settings(tenant_id, settings)
    """
```

Subclases existentes se vuelven thin:
- `BrandExtractionOrchestrator(BaseExtractionOrchestrator[BrandService, Brand, BrandSettings])`
- `OfferExtractionOrchestrator(BaseExtractionOrchestrator[OfferService, Offer, OfferSettings])`

### Pasos (cuando aplique)

1. Extraer signatura común. Identificar los 4 hook points.
2. Crear `BaseExtractionOrchestrator` en `shared/application/extraction/`.
3. Refactor brand → subclass. Assert tests per-wave-save siguen pasando.
4. Refactor offer → subclass. Assert tests siguen pasando.
5. Introducir 3er módulo sobre la base.

### Invariantes a preservar
- Test `test_extraction_orchestrator_per_wave_save` de ambos módulos sigue pasando sin cambios (o adapta el ratchet)
- Trace collectors siguen funcionando
- Progress callbacks reciben misma signature
- Spanish section labels resuelven correctamente

### Criterio de done
- Base en `shared/`
- Brand + offer orchestrators como thin subclasses
- Tests green
- Docs: sección en `.claude/rules/backend-ddd.md` sobre el patrón
- Arch test que valida "nuevos módulos de extracción heredan de BaseExtractionOrchestrator"

### Estimación
4-6h cuando se dispare.

### Señal disparadora
Ticket o mención de: nueva extracción para `landing`, `buyer_persona`, `asset`, `connections`. Si 4-6 meses pasan sin ese ticket, este item muere (no es deuda real, es "nice to have").

---

## Item 4 — `pending_field_paths` en flujos free-form (no guided)

### Objetivo
Prevenir que el copilot pregunte campos ya llenos cuando el user NO está en guided mode.

### Contexto actual
- En guided: `_build_guided_layer` computa `pending_field_paths` leyendo entity data real y pasa al prompt. LLM ve "campos pendientes" explícitos. ✓
- En free-form (sin guided): el LLM tiene el `completion_snapshot` (por sección, no per-field) pero no sabe con precisión qué paths están llenos. Puede re-preguntar.

### Escenarios afectados
1. User en `/brand-studio/identity` sin guided, escribe "mi marca se llama X". LLM captura con `extract_structured`. Turn siguiente user pregunta "¿qué más necesito completar?" — LLM podría listar campos ya llenos porque no sabe el estado per-field.
2. User post-extracción (URL/doc ya ejecutado), sale de guided, vuelve a preguntar desde chat libre — mismo problema.

### Propuesta

**Opción A (recomendada)**: Inyectar snapshot per-field en el system prompt cuando `ClientContext.current_route` matchea un studio.

- Nueva función `_build_studio_snapshot_layer(state)` en `orchestrator/graph.py`:
  - Lee `current_route` de client_context
  - Si matchea `/brand-studio/*` o `/offer-studio/*`:
    - Calcula campos filled vs empty del módulo
    - Renderiza sub-template con lista de filled y empty paths
  - Si no matchea, retorna ""

**Opción B**: Tool `get_entity_completion` que el LLM invoca on-demand.
- Menos intrusivo en prompt.
- Requiere que el LLM acuerde de llamarlo.
- Desventaja: latencia extra.

Ir con Opción A — consistente con cómo guided maneja pending_paths.

### Pasos

1. Extraer helper compartido entre guided y studio snapshot:
   `_compute_field_completion(domain, entity_id, tenant_id) -> (filled: list, empty: list)`.
   Refactor del actual `_compute_pending_field_paths` (graph.py:197) para reusar.

2. Nuevo template `copilot_studio_snapshot.j2`:
   ```jinja2
   {% if studio_route %}
   --- ESTADO ACTUAL DE {{ module_label }} ---
   Ruta: {{ current_route }}
   Campos ya completados ({{ filled|length }}): {{ filled|join(", ") }}
   Campos todavía vacíos ({{ empty|length }}): {{ empty|join(", ") }}
   
   No preguntes por campos completados — ya están. Si el user quiere
   cambiar uno, úsalo como contexto y llama propose_field_updates.
   --- FIN ESTADO ---
   {% endif %}
   ```

3. En `build_system_prompt`:
   ```python
   base = ...  # existing
   guided_layer = _build_guided_layer(state)
   studio_layer = _build_studio_snapshot_layer(state) if not guided_layer else ""
   return base + guided_layer + studio_layer
   ```

   Si guided está activo, skip studio layer (guided ya lo cubre).

4. Tests:
   - `test_studio_snapshot_layer.py`: matchea `/brand-studio/*`, `/offer-studio/*`, vacío en otras rutas.
   - Integration: verificar que LLM no pregunta por campos listados como filled (smoke test con mock LLM).

### Invariantes
- `_compute_pending_field_paths` de guided sigue igual (o comparte helper).
- No afecta perf: máximo 1 DB read por turno (ya lo hacemos via `_get_completion_snapshot`).
- Sin guided activo, current_route en `/dashboard` u otra no-studio → layer vacío, sin overhead.

### Criterio de done
- Helper `_compute_field_completion` compartido guided + studio
- Template `copilot_studio_snapshot.j2` implementado
- Tests nuevos pasan
- Traza manual en navegador (chrome-devtools-verify) valida: user en /brand-studio/identity sin guided, escribe algo, próximo turn LLM sabe qué falta
- Sin regresión en tests existentes de guided

### Estimación
2-3h.

---

## Orden de ejecución sugerido

```
1. Item 1 (Audit review)       — alta prioridad, feedback loop del commit recién hecho
2. Item 2 (test_streaming)     — alta prioridad, desbloquea /test-backend native CI
3. Item 4 (pending free-form)  — media prioridad, cierra brecha UX post-extracción
4. Item 3 (base class DRY)     — deferred hasta 3er módulo de extracción
```

Items 1 y 2 pueden hacerse en paralelo (distintos archivos). Item 4 usa conocimiento de items 1+2 si hubo findings relevantes.

## Comandos de arranque en nueva conversación

```bash
# Contexto
cd /home/chris/AISALESHT
git log --oneline -5
cat docs/mejoras-proceso/copilot-extraction-unified-design.md
cat docs/mejoras-proceso/tech-debt-plan-post-extraction-unified.md

# Baseline de estado
git status --short
/estado

# Confirmar que el commit base existe
git show --stat 8d0a63d3 | head -30
```

## Criterio de done global del plan

Los 4 items cerrados (o Item 3 diferido con señal disparadora documentada) + arch tests + test-backend native + /test-all green.
