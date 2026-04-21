# PLAN — Brand Studio "Estilo Comunicacional"

**Input:** `FLOW-SPEC.md` (this folder).
**Execution orchestrator:** `/nicolify-feature` (full-stack) O ejecutar fases manualmente con `backend-expert` + `frontend-expert`.

---

## Fases

### Fase 0 — Contract Lock (arquitecto) · 1h

**Owner:** nicolify-architect o revisión manual.

**Deliverables:**
- `CONTRACT.md` con DTOs exactos (`PresetSummaryDTO`, `PersonalityProfileDTO`, `SelectPresetRequest`, `UpdateDimensionsRequest`, `SimulationDTO`, `CloneRequest`, `ActivateRequest`, `FromVoiceToneRequest`) y paths.
- Tipado compartido en TypeScript derivado del backend (`features/brand-studio/types/personality.ts`).

**Acceptance:**
- Contract cubre los 7 endpoints existentes + 3 nuevos (`/clone` full impl, `/{id}/activate`, `/from-voice-tone`).
- Frontend y backend firman el mismo shape.

---

### Fase 1 — Backend clone pipeline + activate + port · 1–2 días

**Owner:** backend-expert + nicolify-agentic (LangGraph wiring).

**Files:**
- `backend/src/modules/brand/api/personality.py` — reemplazar 501 en `/clone`, agregar `/{id}/activate` y `/from-voice-tone`.
- `backend/src/modules/brand/application/services/personality_service.py` — 3 nuevos métodos.
- `backend/src/modules/brand/application/agents/style_analyzer/graph.py` — verificar `personality_app` es invocable standalone; agregar adapter si hace falta.
- `backend/src/shared/links/ports/personality.py` — **NEW** port con `get_active(tenant_id) -> PersonalityProfileDTO | None`.
- `backend/tests/modules/brand/test_personality_api.py` — cover clone, activate, from_voice_tone.
- `backend/tests/architecture/test_ddd_boundaries.py` — ajustar allowlist si aparece nuevo cross-import esperado vía port.

**Acceptance:**
- `POST /personality/clone` con text_input de 30+ mensajes retorna 201 con PersonalityProfileDTO `is_active=false` y `anchor_count>0`.
- `POST /personality/{id}/activate` deactiva perfil anterior + activa el target. Idempotente.
- `POST /personality/from-voice-tone` lee `BrandIdentity.voice_tone` del tenant, retorna profile con `profile_type="migrated_from_voice_tone"`.
- Port se importa desde `shared/links/ports/personality` — ningún cross-module import directo.
- TDD cumplido: tests RED → GREEN.
- Tenant isolation verificado (cada query filtra por tenant_id).

**Verification:**
```bash
cd backend && .venv/bin/pytest tests/modules/brand/test_personality_api.py -v
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd backend && .venv/bin/ruff check src/modules/brand/ --no-cache
```

---

### Fase 2 — Frontend sección + schema cleanup · 2–3 días

**Owner:** frontend-expert + nicolify-ux-designer (validación).

**Files:**
- `frontend/src/features/brand-studio/lib/section-catalog.ts` — insert slug `estilo` en posición 3, icon `MessageCircle`.
- `frontend/src/features/brand-studio/pages/section-page-map.ts` — registrar `estilo: CommunicationStylePage`.
- `frontend/src/features/brand-studio/pages/section-pages/CommunicationStylePage.tsx` — **NEW** Server Component.
- `frontend/src/features/brand-studio/components/communication-style/` — **NEW folder** con 9 componentes (ver FLOW-SPEC §9).
- `frontend/src/features/brand-studio/api/personality-api.ts` — **NEW**.
- `frontend/src/features/brand-studio/hooks/use-personality.ts` — **NEW**.
- `frontend/src/features/brand-studio/schemas/identity.schema.ts` — remove líneas 42–70 (`voice_tone`, `voice_tone_clone`).
- `frontend/src/features/brand-studio/schemas/voice.schema.ts` — **DELETE FILE**.
- `frontend/src/features/brand-studio/actions/registry.ts` — remove `"voice-clone"` action key.
- `frontend/src/features/brand-studio/actions/placeholders.tsx` — delete `VoiceClonePlaceholder`.

**Acceptance:**
- Navegando a `/{tenantId}/brand-studio/estilo`:
  - Sin profile activo → EmptyState con 2 CTAs + (si `voice_tone` legacy) migration card.
  - Con profile activo → ActiveState con dimensiones, huella, ejemplos, botones.
- Preset picker drawer lista los 6 presets desde `GET /personality/presets`. Seleccionar uno activa el perfil y vuelve a ActiveState.
- Clone wizard ejecuta los 3 pasos. Paso 2 muestra estado de progreso (polling del job hasta completion).
- Sliders de dimensiones hacen PUT debounced (500ms) y refrescan ejemplos.
- Identity page ya no muestra campos de voz.
- Arch fitness tests pasan (PascalCase, kebab-case, no cross-feature dupes, fetchClient en api/).
- 0 ESLint errors nuevos. TSC clean.

**Verification:**
```bash
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/features/brand-studio/
cd frontend && npx vitest run src/features/brand-studio/
cd frontend && npx vitest run src/__tests__/architecture/
```

---

### Fase 3 — Downstream wiring (sales_agent + copy) · 1–2 días

**Owner:** sales-agent-expert + backend-expert.

**Files:**
- `backend/src/modules/sales_agent/...` — inyectar `personality_port.get_active(tenant_id)` al componer el system prompt del graph. Patrón referencia: commit `4402939d` (guardrails wiring).
- Landing copy generator, asset captions: migrar de leer `BrandIdentity.voice_tone` a leer `PersonalityProfile.system_instruction`. Identificar servicios:
  ```bash
  cd backend && grep -rn "voice_tone" src/modules/ --include="*.py" | grep -v test
  ```
- Tests de integración: 1 tenant con preset activo → SDR response incorpora tono del preset. 1 tenant sin profile activo → fallback genérico.

**Acceptance:**
- Un tenant con preset `electric` recibe respuestas con MAYÚSCULAS + emojis 🔥🚀.
- Un tenant con preset `minimalist` recibe respuestas de 1-2 líneas sin emojis.
- Un tenant sin personality configurada sigue funcionando (fallback string genérico).
- No cross-module imports directos — solo via `shared/links/ports/personality`.

**Verification:**
```bash
cd backend && .venv/bin/pytest tests/modules/sales_agent/ -v
cd backend && .venv/bin/pytest tests/integration/ -v -k personality
```

---

### Fase 4 — Cleanup + docs · 0.5 día

**Files:**
- `docs/domains/brand/communication-style.md` — documenta catálogo + consumers + trade-offs.
- `.claude/rules/brand-personality.md` — regla opcional para evitar duplicar voice en otros schemas.
- Opcional: migration Alembic para stamp `BrandIdentity.voice_tone` como `deprecated=True` si existe patrón similar.

**Acceptance:**
- Doc accesible desde `docs/domains/INDEX.md`.
- CLAUDE.md rule mencionada si el catálogo es canónico.

---

## Orden de implementación

Ejecutar **estrictamente en orden**:

1. Fase 0 (Contract Lock) ← necesario para paralelizar 1 y 2.
2. Fase 1 (Backend) + Fase 2 (Frontend) pueden correr en paralelo tras Fase 0, siempre que FE mockee respuestas hasta que BE esté listo.
3. Fase 3 (Downstream wiring) espera a Fase 1 completa.
4. Fase 4 (Cleanup) al final.

**Tiempo estimado total:** 4–6 días de trabajo efectivo con 2 agentes en paralelo tras Fase 0.

---

## Riesgos y rollback

| Riesgo | Mitigación |
|---|---|
| Clone pipeline tarda >4 min para muestras grandes | Paso 2 soporta cerrar ventana + polling; notifica al volver. `PersonalityProfileModel` acepta `is_active=false` mientras se procesa. |
| `BrandIdentity.voice_tone` referenciado en más sitios de los detectados | Antes de Fase 2, grep exhaustivo: `grep -rn "voice_tone" backend/src frontend/src`. Si aparecen consumidores no contemplados, escalar a Fase 3. |
| Tenants antiguos pierden continuidad si migración automática marra | Card de migración es opcional (user puede elegir "empezar de cero"). Legacy `voice_tone` nunca se borra hasta sprint final. |
| Sidebar con 14 secciones se vuelve largo | Aceptable por ahora. Si excede 15+, rediseñar navegación (otro sprint, otra sesión ux-flow-architect). |

**Rollback plan:** todos los cambios son aditivos excepto los deletes en schema/actions. Revertir por commit si algo explota en prod:

1. `git revert <frontend cleanup commit>` ← restaura voice_tone fields en identity.
2. `git revert <backend clone impl commit>` ← vuelve `/clone` a 501.
3. La nueva sección `estilo` se deja registrada pero vacía; no rompe identity.
