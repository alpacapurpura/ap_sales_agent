# Prompt — PM close loop

> Copy-paste este prompt al volver a sesión `/pm` para cerrar el PR.

```
/pm

PR-1-voice-media-hardening terminó implementación + auditoría. Cierro el loop.

Lee:
- `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-1-voice-media-hardening/IMPL-LOG.md`
- `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-1-voice-media-hardening/REVIEW.md`
- Último commits: `git log --oneline -10`

Hacer:
1. Escribir `RESULT.md` siguiendo template (`process/pr-folder-template/RESULT.md`):
   - Outcome real vs esperado
   - Surface entregada concreta
   - Capacidades nuevas con lineage
   - Decisiones tomadas durante implementación
   - Métricas si aplican
   - Deuda técnica generada
2. Update `current-state/copilot.md` con bloque "Capacidades" copiado de RESULT.md.
3. Append decisiones relevantes a `pis/active/PI-2-copilot-improvement/decisions.md`.
4. Append learnings de este PR a `sprints/S1-*/learnings.md`.
5. Cambiar `Estado: shipped` en `PR.md`.
6. Si última PR del sprint → llenar `handoff.md` para sprint siguiente.
7. Decirme próximo paso: ¿siguiente PR del sprint? ¿abrir nuevo? ¿cerrar sprint?

Quiero brief al final < 200 palabras con qué shipped + qué cambió en producto.
```

## Notas

- `/pm` no inventa el RESULT — extrae info de IMPL-LOG + REVIEW + git log.
- Si REVIEW.md tiene veredicto != `approve` → `/pm` NO escribe RESULT, escala a Chris para decidir.
- `current-state/copilot.md` es donde "el producto" se actualiza. PR-folder es histórico.
