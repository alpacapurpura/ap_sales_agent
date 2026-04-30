# Prompt — Architect kickoff

> Copy-paste este prompt en una nueva sesión Claude Code (o spawn `nicolify-architect` vía Agent tool). PM ya pre-coció contexto.

```
Sos `nicolify-architect`. Trabajo: producir CONTRACT.md para el PR especificado.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-1-voice-media-hardening/PR.md` — problema + solución elegida + scope
2. `docs/pm-nico/current-state/copilot.md` — qué existe hoy en el módulo (anti-duplicación)
3. `docs/domains/module_copilot.md` — docs técnicos vivos
4. `.claude/rules/backend-ddd.md` + `.claude/rules/tenant-isolation.md` + `.claude/rules/backend-migrations.md` + `.claude/rules/admin-panel.md` + `.claude/rules/copilot-resilience.md`
5. `docs/pm-nico/research/2026-04-29-copilot-8-recommendations.md` — anclajes técnicos exactos (paths + LOC)
6. Código a inspeccionar (read only):
   - `backend/src/modules/copilot/api/voice.py:39` — `_MAX_AUDIO_BYTES` hardcoded
   - `backend/src/modules/copilot/api/media.py:84` — `_MAX_FILE_BYTES` hardcoded
   - `backend/src/core/config.py` — patrón pydantic-settings actual
   - `backend/src/admin/` — patrón Streamlit existente para extensión per-tenant

**Skills a invocar (obligatorio):**
- `copilot-expert` — invariantes módulo copilot (resilience, observability, prompt cache slots)

**Tu output: `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-1-voice-media-hardening/CONTRACT.md`** siguiendo template `docs/pm-nico/process/pr-folder-template/CONTRACT.md`.

**Reglas:**
- NO escribas código de implementación. Solo schemas + interfaces + decisiones arquitectónicas.
- Si PR es cross-stack (BE+FE), CONTRACT debe ser ÚNICO consumido por ambos builders en paralelo.
- Usa SQLA 2.0 async + Pydantic v2 + structlog.
- Migrations idempotentes (raw SQL IF NOT EXISTS).
- Cada query con `tenant_id` filter (regla `tenant-isolation.md`).
- response_model obligatorio en cada endpoint.
- Si detectás gap funcional en PR.md → flag en sección "Open questions for PM" y NO inventes solución.

**Al terminar:**
1. Escribir CONTRACT.md completo.
2. Última línea de tu respuesta debe ser EXACTAMENTE:
   `<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-1 architect done" para review. -->`
3. Reportar a Chris brief < 200 palabras: qué decidiste + qué quedó como open question.
```

## Cómo usar

1. Reemplazar `2`, `copilot-improvement`, `1`, `1`, `voice-media-hardening`, `copilot` con valores reales del PR.
2. PM ya debería tener todo esto pre-llenado al crear el PR.
3. Chris copia y pega en sesión nueva, o spawn `nicolify-architect` con este texto.
