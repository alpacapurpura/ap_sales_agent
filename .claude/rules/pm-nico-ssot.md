---
globs: "docs/pm-nico/**"
description: Stub — invoca pm skill
---

# PM-Nico SSoT

`docs/pm-nico/` = SSoT funcional Nicolify presente+futuro. Owner único = `/pm` skill.

**Cuando aplicar:** sesión que modifica funcionalidad **user-facing** (api/, application/services, nuevas pantallas, copilot tools nuevos, conexiones nuevas, migraciones que cambian shape user-facing) → update `docs/pm-nico/current-state/{module}.md`.

**No aplica:** refactor interno sin cambio user-facing, bug fix sin capacidad nueva, tests/CI/lint, docs técnicos `docs/domains/`.

Detalle (qué actualizar, secciones, cuándo notificar `/pm`, anti-patterns) en `pm` skill → `references/pm-nico-ssot.md`.

**Anchor:** antes commit cambio funcional → revisar `current-state/{m}.md` necesita update. Antes `gh pr create` → confirmar refleja realidad.
