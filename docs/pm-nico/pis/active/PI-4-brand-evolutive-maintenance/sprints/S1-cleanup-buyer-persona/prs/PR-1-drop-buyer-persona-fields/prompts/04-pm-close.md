# Prompt — PM close loop (PR-1 drop-buyer-persona-fields)

> Copy-paste este prompt al volver a sesión `/pm` para cerrar el PR.

```
/pm

PR-1-drop-buyer-persona-fields del PI-4-brand-evolutive-maintenance / S1 terminó implementación + auditoría cross-stack. Cierro el loop.

Lee:
- `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/IMPL-LOG.md` (secciones BE + FE)
- `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/REVIEW-backend.md`
- `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/REVIEW-frontend.md`
- Últimos commits: `git log --oneline -15`

**Validar antes RESULT:**
- Ambos REVIEWs deben dar PASS. Si uno tiene WARN → ok pero anotar deuda. Si uno FAIL → STOP, escalá a Chris (no escribir RESULT).

Hacer:
1. Escribir `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/RESULT.md` siguiendo template (`process/pr-folder-template/RESULT.md`):
   - Outcome real vs esperado (form más corto, fields eliminados sin regresión)
   - Surface entregada concreta (migration commit + paths cleanup BE/FE/copilot)
   - Capacidades modificadas con lineage (Buyer Persona → secciones eliminadas)
   - Decisiones tomadas durante implementación (¿backup data ejecutado? ¿1 o 2 migrations? ¿fixtures actualizados todos?)
   - Métricas si aplican (form length reduction, # tests verdes)
   - Deuda técnica generada (cualquier WARN del REVIEW)

2. Update `docs/pm-nico/current-state/brand.md`:
   - Sección "Capacidades actuales" / "Buyer Personas" — anotar deprecación de objections + preferred_channels con lineage (PR-1, commit hash, fecha)
   - Sección "Capacidades deprecadas" (crear si no existe) — agregar entries con commit-antes-de-remover

3. Append decisiones relevantes a `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/decisions.md`.

4. Append learnings de este PR a `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/learnings.md`:
   - Qué funcionó (e.g., "Explore brief redujo discovery a 1 turn")
   - Qué no funcionó / sorpresas (si aparecieron en implementation)
   - Acciones para próximos sprints rolling

5. Cambiar `Estado: shipped` en `PR.md`.

6. Decidir cierre sprint S1:
   - Si Chris no tiene más feedback brand → llenar `handoff.md` indicando "track espera nuevos items"
   - Si Chris trae nuevo feedback → abrir S2 con sprint.md nuevo

7. Decirme próximo paso: ¿abrir S2 con nuevo feedback brand? ¿pausar PI-4 (sigue activo, sin sprint en progreso)? ¿mover sprint S1 a done y esperar?

Quiero brief al final < 200 palabras con qué shipped + qué cambió en producto + estado track PI-4.
```

## Notas

- `/pm` no inventa el RESULT — extrae info de IMPL-LOG + REVIEWs + git log.
- Si REVIEW-backend.md o REVIEW-frontend.md tiene veredicto FAIL → `/pm` NO escribe RESULT, escala a Chris para decidir.
- `current-state/brand.md` es donde "el producto" se actualiza. PR-folder es histórico.
- PI-4 es rolling: no se cierra al cerrar PR-1. Sigue activo esperando próximos items maintenance.
