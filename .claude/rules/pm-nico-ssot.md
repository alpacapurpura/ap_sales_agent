# PM-NICO SSoT — Update Obligatorio

`docs/pm-nico/` es la SSoT funcional Nicolify presente + futuro. Owner único = `/pm` skill. Rule always-loaded.

## Cuándo aplica

Cualquier sesión Claude Code que **modifique funcionalidad user-facing** de un módulo (no solo refactor interno) DEBE actualizar `docs/pm-nico/current-state/{module}.md`.

Aplica a:
- Backend: cambios en `api/`, `application/services/`, nuevos endpoints, nuevos workflows
- Frontend: nuevas pantallas, modificaciones flujos user, nuevos features visibles
- Copilot tools nuevos (afectan capacidades operables conversacionalmente)
- Conexiones nuevas (afectan capacidades del módulo)
- Migraciones que cambian shape de datos user-facing

NO aplica a:
- Refactor interno sin cambio user-facing
- Bug fix que no introduce capacidad nueva
- Tests, CI, lint, type fixes
- Docs técnicos (`docs/domains/`)

## Qué actualizar

`docs/pm-nico/current-state/{module}.md` (16 átomos posibles). Secciones a tocar:

| Cambio | Sección |
|---|---|
| Capacidad nueva | "Capacidades actuales" |
| Capacidad ahora operable copilot | "Capacidades operables desde copilot" |
| Mejora calidad existente | "Estado calidad funcional" |
| Cierre PI | "PIs históricos" |
| Decisión producto registrada | "Decisiones producto vinculadas" |
| Última edición | "Meta" → "Última actualización" |

Mantener caveman style. Bullets > párrafos. Tablas.

## Cuándo update PI/PR

Si trabajo está dentro PI activo:
- Update `docs/pm-nico/pis/PI-{N}-{theme}/decisions.md` (decisiones tomadas durante implementación)
- Si PR shipped: actualizar PR.md estado → `shipped` + update current-state

## Cuándo notificar `/pm`

Si modificación NO está alineada con `current-state/` previo (ej: agregaste capacidad sin PR formal), **flag al user**:

> "Este cambio agrega capacidad funcional al módulo X. Para mantener SSoT funcional, considera invocar `/pm` para registrarlo formalmente, o yo puedo updatear `current-state/{module}.md` directamente. ¿Cuál prefieres?"

NO updatear silenciosamente sin notificar — corre riesgo de drift entre lo planeado (PR) vs. lo construido.

## Anti-patterns

- ❌ Modificar dominio + skip update → SSoT funcional decae rápido.
- ❌ Update con jerga técnica (`docs/domains/` style). `current-state/` es vista user-facing negocio.
- ❌ Update sin tocar "Última actualización" — pierde rastro de freshness.
- ❌ Crear `current-state/` átomo nuevo sin appendear a `INDEX.md` mapa.
- ❌ Modificar producto sin pasar por `/pm` cuando es feature significativo (no solo bug).

## Anchor

- Antes commit con cambios funcionales → revisar si `current-state/{m}.md` necesita update.
- Antes hacer PR técnico (gh pr create) → confirmar `current-state/` refleja realidad.
- Si `/pm` skill orchestrating → el mismo PM updatea (no Chris).
- Si trabajo cross-skill (sin `/pm` activo) → update silencioso si ya hay PR shipped, NOTIFY si capacidad nueva no planeada.
