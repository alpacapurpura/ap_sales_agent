# F3 — Brand Summary "lighthouse"

**Pre-req:** F1 cerrada (provider discovery). Paralelizable con F2/F6/F7.
**Sprints estimados:** 1.
**Bloquea:** F4 (URL contextual usa brand summary para evaluar relevancia).
**Valor entregado:** la marca está presente en cada respuesta. El usuario nota coherencia transversal.

---

## §1 Objetivo

Crear **documento vivo** de la marca: tabla `brand_summary` ≤800 chars caveman español neutro, regenerada via event-driven cuando se modifica brand. Auto-inyectar en system prompt del copilot cuando target_route ∈ {offer-studio, landing, campaign, sales-related}.

Es el equivalente a CLAUDE.md del proyecto, pero específico de la marca del tenant.

---

## §2 Pre-lectura específica

- `02-architecture-target.md §4` (BrandSummary table + flow).
- `backend/src/modules/brand/` (entender BrandSettings + repository.save).
- `.claude/rules/backend-migrations.md` (idempotente).
- `learnings/F1-*.md` y `learnings/F2-*.md` (si existen al arrancar).
- Plantilla prompt: `backend/src/modules/copilot/infrastructure/prompts/` (estructura existente).

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `LLM brand voice summary distillation prompt 2026 best practices`
- `event-driven domain events FastAPI ARQ async handler 2026`
- `OpenAI structured output brand description short concise 2026`

Productos:

- Patrón de prompt para destilar identidad (≤800 chars) — incluir tono, promesa, avatar, diferenciador.
- Versionado del summary (regen frecuente vs estable).

---

## §4 Lo que NO se toca

- BrandSettings schema (Pydantic) y repos existentes.
- Frontend Brand Studio.
- Routing tier.
- §3 general de no-tocar.

---

## §5 Deliverables

### 5.1 Migration

```sql
CREATE TABLE IF NOT EXISTS brand_summary (
    tenant_id UUID PRIMARY KEY,
    summary TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    model_used TEXT NOT NULL,
    chars_count INT NOT NULL CHECK (chars_count <= 1000),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_section_changed TEXT NULL
);
```

Idempotente (`IF NOT EXISTS`). Test en clone DB.

### 5.2 Domain event

`backend/src/shared/events/brand_section_updated.py`:

```python
@dataclass(frozen=True)
class BrandSectionUpdated:
    tenant_id: UUID
    section: str
    changed_fields: tuple[str, ...]
    occurred_at: datetime
```

Emitido por `BrandRepository.save_section()` y `save()`.

### 5.3 ARQ task: regen_brand_summary

`backend/src/shared/workers/brand_summary_regen.py`:

- Fetch BrandSettings completo del tenant.
- Render prompt `prompts/brand_summary_caveman.j2` (Jinja) con few-shot.
- LLM tier NANO con `response_format={"type": "json_schema", ...}` para estructurar.
- Validate ≤800 chars. Si excede, retry con instrucción más estricta (max 1 retry).
- UPSERT con `version` incremental.

Trigger:

- Handler suscrito a `BrandSectionUpdated` → encola task ARQ con dedupe key (tenant_id) y debounce 30s (evita regen explosivo en saves consecutivos del mismo tenant).

### 5.4 Brand provider context_injector

`backend/src/modules/brand/copilot_provider/context_inject.py`:

```python
class BrandContextInjector:
    INJECTION_ROUTES = ("offer-studio", "landing", "campaign", "sales")

    async def inject_for(self, target_route: str, tenant_id: UUID) -> str | None:
        if not self._matches_any(target_route, self.INJECTION_ROUTES):
            return None
        summary = await self._repo.get(tenant_id)
        if summary is None:
            return None
        return f"## Brand Lighthouse\n{summary.summary}\n\nToma decisiones desde aquí. Si algo es incoherente, dilo."
```

### 5.5 System prompt integration

`copilot/application/context_builder.py` (puede ya existir o crearse en F2):

- Itera providers activos vía discovery → llama `context_injector.inject_for(route, tenant_id)`.
- Concatena en system prompt como **prefijo estable** (cacheable).
- Order: brand_lighthouse → otros context_injectors → completion_snapshot → studio_snapshot → workflow_state.

### 5.6 Backfill + admin tools

- Script `backend/scripts/backfill_brand_summaries.py` — corre `regen_brand_summary` para todos los tenants con BrandSettings.
- Admin Streamlit `/admin/brand/summaries` — lista, regen manual, ver historial versions (mínimo: tabla + botón regen).

### 5.7 Tests

- Unit del prompt rendering + validation ≤800 chars.
- Integration: `BrandRepository.save()` emite event → handler → ARQ → tabla actualizada.
- Arch test: si fields críticos brand (`identity`, `positioning`, `voice`, `narrative`) cambian sin trigger → fail. Lista de campos críticos en código + arch test.
- Golden test: copilot en `/offer-studio` muestra que brand_summary está en system prompt (assert `"Brand Lighthouse"` en prompt rendered).

---

## §6 Quality gates

- `/test-backend` verde.
- Migration aplicada en clone DB sin errores.
- Backfill corrido en dev → todos los tenants con BrandSettings tienen `brand_summary` ≤800 chars.
- Manual: editar campo en Brand Studio → en <60s el `brand_summary` se regenera. Verificar con admin Streamlit.

---

## §7 Riesgos

| Riesgo | Mitigación |
|---|---|
| Summary mal generado degrada respuestas | LLM-judge antes de UPSERT (sample 50 primeros, manual review). Retry con prompt estricto. |
| Regen explosivo | Debounce 30s + dedupe key. |
| Token budget del system prompt sube | Cap 800 chars duro + prompt-cache mitiga costo. |
| BrandSettings vacío en tenant nuevo | Skip injection (return None) hasta que haya datos. |

---

## §8 Definición de hecho

- [ ] Migration idempotente aplicada.
- [ ] Domain event emitido + handler suscrito.
- [ ] ARQ task funcional con dedupe.
- [ ] Brand provider context_injector.
- [ ] System prompt incluye lighthouse en routes target.
- [ ] Backfill script + corrido.
- [ ] Admin Streamlit listo.
- [ ] Tests + arch tests verdes.
- [ ] Golden F0 + F2 verdes.
- [ ] `learnings/F3-brand-summary.md` + `prompts/F4-start.md`.

---

## §9 Notas para F4

- API del context_injector está documentada para que F4 (URL inspiraciones) se sume al system prompt sin romper.
- Si el summary es estable, F4 puede asumir prompt cache hit alto.
