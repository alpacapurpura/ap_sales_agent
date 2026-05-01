# RESULT — PR-{N}-{slug}

> Owner: `/pm`. Cierre del loop. Sin este archivo, PR NO se considera shipped. PM extrae info de IMPL-LOG.md + REVIEW.md + commits.

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped |
| Fecha cierre | YYYY-MM-DD |
| Commits | {hashes principales} |
| Branch merged a | development |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| {outcome 1} | ... | ... | ... |
| {outcome 2} | ... | ... | ... |

Veredicto: ✅ cumplido | ⚠️ parcial | ❌ no cumplido

## Surface entregada (concreta)

| Tipo | Path / nombre | Notas |
|---|---|---|
| Tabla DB | ... | migration `{timestamp}_xxx` |
| API endpoint | ... | response_model X |
| Domain type | ... | en `modules/{m}/domain/...` |
| FE component | ... | en `features/{m}/components/...` |
| Service | ... | en `modules/{m}/application/services/` |

## Capacidades agregadas (lineage para current-state)

```md
### Cap: {nombre capacidad}
- Introducida: PR-{N} (PI-{X}, S{N}, commit {hash}, {fecha})
- Estado: live
- Operable copilot: {sí/no/parcial} ({tools si aplica})
```

(Bloque que PM copia a `current-state/{módulo}.md` sección Capacidades.)

## Decisiones tomadas durante implementación

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| D-... | ... | ... | IMPL-LOG / REVIEW |

(Las relevantes se appendan también a `decisions.md` del PI.)

## Métricas medidas (si aplican)

| Métrica | Baseline | Cierre PR | Delta |
|---|---|---|---|
| ... | ... | ... | ... |

## Deuda técnica generada

| Item | Razón | Sprint destino |
|---|---|---|
| ... | ... | ... |

## Update obligatorios hechos

- [ ] `current-state/{módulo}.md` actualizado con capability lineage
- [ ] `decisions.md` PI appendeado
- [ ] Sprint `learnings.md` appendeado
- [ ] Si capability deprecada → bullet en sección `## Capacidades deprecadas`
- [ ] Si última PR del sprint → handoff.md llenado

## Próximo paso PM

- {Si quedaron cosas → siguiente PR del sprint, o discovery nuevo}

---

PR-{N} **shipped**. PM cierra archivo. Loop completo.
