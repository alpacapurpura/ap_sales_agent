# REVIEW-final.md — Template (auditor del story completo)

> Owner: `/auditor`. Solo después que TODOS los tickets del story estén `audit-passed`.
> Verificación end-to-end del story como un todo (no ticket-por-ticket).

---
story_id: STORY_ID
sprint: SN
pi: PI-N
audited_at: 2026-05-04T18:30Z
auditor_model: claude-opus-4-7
verdict: APPROVED                                # APPROVED | CHANGES_REQUESTED
ready_to_merge: true
---

## Tickets cubiertos

| Ticket | Tipo | Owner | Verdict | SHA |
|---|---|---|---|---|
| T-1 | backend | qwen-opencode | APPROVED | abc1234 |
| T-2 | agentic | claude-opus-4-7 | APPROVED | def5678 |
| T-3 | frontend | qwen-opencode | APPROVED | 9876fed |

## End-to-end verification

> Más allá de tests por ticket — testear el story como user real.

### Test E2E (Playwright si ui-story, eval suite si agentic-story)

```
$ cd frontend && npm run test:e2e:smoke -- --grep "{story-id}"
[paste output]
```

> O agentic:
```
$ cd backend && .venv/bin/pytest tests/agentic_evals/{module}/{story_id}_eval.py --trials=3
[paste output]
pass^3 score: 0.83 (>= 0.5 threshold) ✅
```

### Smoke test manual (si aplica)

- [ ] Dev server up (`make dev`)
- [ ] Naveg `https://dev-app.nicolify.com/{path}`
- [ ] Acción reproducida → outcome esperado verificado
- [ ] Edge cases: cross-tenant tested, mobile responsive verified

## Story-level acceptance (del 01-spec.md)

| Scenario | Type | Verifier | Estado |
|---|---|---|---|
| `happy-path` | happy | e2e + state_check | ✅ |
| `invalid-input` | negative | e2e | ✅ |
| `concurrent-edit` | edge | e2e | ✅ |
| `cross-tenant-leak` | adversarial | e2e + state_check | ✅ |

## Cross-cutting checks

- ✅ Story YAML refleja realidad (status `live`, scenarios type=regression para los live)
- ✅ Capability YAML actualizado (status derivado de stories)
- ✅ Module doc `product/modules/{m}.md` refleja capability nueva
- ✅ Spanish neutro en strings user-facing
- ✅ Telemetría: events emitidos vistos en logs locales
- ✅ Performance: latencia p95 medida y bajo threshold

## Test coverage delta del story

```
Module                  Before   After    Delta
backend/{m}             81.2%    87.4%    +6.2%
frontend/features/{m}   24.5%    29.8%    +5.3%
```

## Eval coverage delta (si agentic)

| Story | Pass^3 antes | Pass^3 después | Status |
|---|---|---|---|
| `{story_id}` | N/A (planned) | 0.83 | promote → live + scenarios → regression |

## Findings residuales (post-merge)

- ⚠️ Performance: cuando hay > 1000 records, list endpoint demora 800ms p95. Crear story de optimización.
- ✅ Sin findings bloqueantes.

## Verdict

**APPROVED** ✅
**ready_to_merge:** true

> /pm puede proceder con `07-merge.md`: aplicar diff a `product/`, actualizar status en stories y capabilities, mover sprint si corresponde.

## Output al orchestrator

```
APPROVED -> ver REVIEW-final.md
story state: ready-to-merge
next: /pm aplica merge
```
