# Fase 09 — Multi-channel projection · ACCEPTANCE

DoD por sub-paso. Cada sub-paso es revertible atómico.

## 09.A — docs (PRE_INVESTIGATION + SPEC + ACCEPTANCE)

**DoD**:
- [ ] PRE_INVESTIGATION.md tiene respuesta evidence-backed a Q1.1, Q1.2,
      Q1.3, Q2.1, Q2.2, Q3.1, Q3.2, Q4.1, Q4.2, Q4.3, Q5.1, Q5.2.
- [ ] SPEC.md describe algoritmo + adapter port + sub-fases.
- [ ] ACCEPTANCE.md (este archivo) lista DoD por sub-paso.
- [ ] STATUS.md `opened_at` set + `baseline_green_commit` apunta al close
      Fase 08 (`2e0f1cc7`).
- [ ] STATE.md `sub_step: 0/7 → A/G done`, `last_updated` bump.
- [ ] Baseline tests confirmados: BE arch 507 / FE arch 38 (capturado
      pre-fase).

## 09.B — `next_question` core + unit tests

**TDD**: tests primero (RED), implementación después (GREEN).

**DoD**:
- [ ] `tests/modules/copilot/test_conversational_questioning.py` cubre:
  - [ ] Empty state retorna primer required field por priority.
  - [ ] Field con valor presente NO se ofrece.
  - [ ] Field con `gate` insatisfecho NO se ofrece.
  - [ ] Field con `gate` satisfecho SÍ se ofrece.
  - [ ] `status=DEPRECATED` excluido.
  - [ ] `can_propose=False` excluido.
  - [ ] Required-first ordering (required-missing > optional-missing).
  - [ ] Tie-break por `(section, -priority, path)`.
  - [ ] Section filter (cuando `section=` provisto).
  - [ ] Empty list `[]` / dict `{}` / blank string `""` cuentan missing.
  - [ ] `False` boolean NO cuenta missing.
  - [ ] Módulo completo retorna None.
  - [ ] Helpers: `_get_path` dotted resolution, `_is_missing`,
        `_gate_satisfied`.
- [ ] Implementación pure-function en
      `copilot/application/orchestrator/conversational_questioning.py`.
- [ ] Test count BE = 695 + N (donde N es count tests nuevos B).
      Sin regression existentes.
- [ ] Type-check + lint clean (`ruff check src/modules/copilot/ tests/modules/copilot/`).
- [ ] Commit conventional: `feat(copilot): next_question algorithm channel-agnostic`.

## 09.C — Web integration (guided advance enrichment)

**DoD**:
- [ ] `advance_guided_setup` tool emite payload extra
      `suggested_field` cuando `next_question` retorna contract.
      Fallback: payload sin enrichment cuando None.
- [ ] Backward compat: tests existentes de `advance_guided_setup`
      siguen verde sin cambios. Si schema del payload se extiende,
      campo adicional opcional.
- [ ] Test nuevo: `test_guided_advance_includes_next_question_hint`.
      Verifica que el bloque actual con un missing field emite hint
      con `human_question_es` (offer) o `_humanize(path)` (brand /
      buyer).
- [ ] FE schemas (frontend/src/features/.../schemas/*.schema.ts)
      NO se tocan (INVARIANT 9).
- [ ] Commit: `feat(copilot): guided advance consume next_question for field hints`.

## 09.D — Channel adapter port + in-memory adapter

**DoD**:
- [ ] Port abstracto en
      `shared/links/ports/conversational_channel.py::ConversationalChannelPort`
      con method abstracto `async ask(contract, context=None)`.
- [ ] Implementación in-memory en
      `copilot/infrastructure/channels/in_memory_channel.py` para tests.
      Captura outbound list[(contract, context)].
- [ ] Test: `test_conversational_channel_port.py` cubre:
  - [ ] Adapter cumple contract abstracto.
  - [ ] In-memory captura ask correcto.
  - [ ] Multiple asks preservan orden.
- [ ] Imports/exports limpios. No tocar BaseChannel ni connections/.
- [ ] Commit: `feat(copilot): conversational channel port + in-memory adapter`.

## 09.E — E2E channel-agnostic

**DoD**:
- [ ] Test `tests/modules/copilot/test_conversational_e2e.py` ejercita:
  - [ ] Setup tenant con offer parcial (algunos required missing).
  - [ ] Loop `next_question → adapter.ask → state.update → next_question`
        hasta None.
  - [ ] Verifica orden esperado de fields preguntados (priority + gate).
  - [ ] Verifica que mismo loop con InMemoryChannel y un fake
        WebChannel produce **misma secuencia** de FieldContract paths.
        (Channel-agnostic = misma decisión, distinto rendering).
- [ ] Test count BE arch ≥ 507 + N. Sin regression.
- [ ] Commit: `test(copilot): e2e channel-agnostic conversational flow`.

## 09.F — Enrichment `human_question_es`

**DoD**:
- [ ] Top required fields cross-module enriched con `human_question_es`
      en español neutro LATAM (sin voseo). Tope ~30 fields total
      distribuídos:
  - [ ] offer: ≥10 fields nuevos populated (sumando los 24 actuales).
  - [ ] brand: ≥10 fields populated (today 0).
  - [ ] buyer_persona: ≥6 fields populated (today 0).
- [ ] `expects: str | None` populated cuando hint type/format ayuda
      (ej. ENUM lista valores, NUMBER hint range, URL hint formato).
- [ ] `gate` populated cuando aplique (ej. brand `tagline` gate=
      `identity.brand_name`).
- [ ] Spanish-text rule check (`.claude/rules/spanish-text.md`):
      tildes, ñ, sin voseo, `tú` no `vos`.
- [ ] Tests existentes siguen verde (catalog projection arch tests).
- [ ] Commit: `chore(field-contract): enrich human_question_es for high-priority required fields`.

## 09.G — Cierre fase

**DoD**:
- [ ] STATUS.md `closed_at` set + status=done.
- [ ] LEARNINGS.md append Fase 09 section con:
  - Pre-fase expectations vs realidad.
  - Resultados cuantitativos.
  - Descubrimientos.
  - Decisiones nuevas.
  - Deuda técnica encontrada (resuelta + tangencial).
  - Cierre del refactor (si aplica) o handoff a próxima fase.
- [ ] STATE.md:
  - `last_updated` bump.
  - `last_green_commit` apunta al close commit.
  - `active_phase` → siguiente o "(refactor cerrado)".
  - `status` → `done` o `next-phase-ready`.
- [ ] HANDOFF.md actualizado con prompt para siguiente fase o cierre.
- [ ] POST_FLIGHT.md ejecutado (test counts post-fase ≥ baseline).
- [ ] Commit: `chore(refactor-field-contract-platform): close Fase 09 + handoff`.

## Rollback plan

Si cualquier sub-paso B-F falla en CI o produce regression:

1. `git revert <hash>` del sub-paso failing.
2. Sub-pasos siguientes que dependan del revertido tampoco se mergean.
3. Investigar root cause antes de re-attempt.
4. Sub-paso A (docs) standalone — no rollback needed.

Si scope explota mid-fase (ej. wiring copilot↔chat real entra en demanda):

1. Cerrar Fase 09 con scope reducido (algoritmo + port + tests + enrichment
   parcial).
2. Abrir Fase 10 dedicada al wiring.
3. ADR nueva justifica el spawn.

## Métrica de éxito Fase 09

- `next_question` cubre 3 módulos (offer/brand/buyer_persona) sin code
  changes per módulo (deriva de FieldContract).
- E2E channel-agnostic confirma misma secuencia en 2+ channels stubbed.
- `human_question_es` populated ≥30 fields total.
- 0 regression copilot acceptance (52 tests existentes verde).
- 0 regression arch tests (≥507 BE + ≥38 FE).
- Refactor field-contract-platform cierra con SSoT `FieldContract`
  cross-module operativo + algoritmo conversational data-driven.
