# Fase 05 — Acceptance Criteria

## Sub-steps atómicos

| # | Sub-step | Descripción | Commit type |
|---|---|---|---|
| 05.A | golden snapshot tests | Capturar agent_identity render + landing builders + completion baseline | `test(refactor-fcp)` |
| 05.B | offer prompt renderer module | Extraer offer-block render de `agent_identity.j2` a Python helper | `refactor(sales_agent)` |
| 05.C | data-driven prompt rendering | Renderer consume contract registry: lifecycle skip + arch test paths ⊆ contract | `refactor(sales_agent)` |
| 05.D | completion contract-driven | `_SECTION_VALIDATORS` derivado de `is_required_semantic` por sección | `refactor(offer)` |
| 05.E | landing builders contract-aware | Builders validan paths via FieldContract (lifecycle skip) | `refactor(landing)` |
| 05.F | tech debt fields gap | Extender contract si pre-investigación detecta gaps | `feat(field-contract)` (opt) |
| 05.G | close phase | LEARNINGS + STATE + STATUS + HANDOFF Fase 06 | `chore(refactor-fcp)` |

## DoD per sub-step

### 05.A — Golden snapshots

- [ ] `tests/modules/sales_agent/test_agent_identity_golden.py` lockea byte-identical render para offer sintético cubriendo todos los fields del template actual.
- [ ] `tests/modules/landing/application/test_landing_builders_golden.py` lockea output de cada builder (transformer, brochure, velvet_rope, flash_offer, squeeze) para offer sintético.
- [ ] `tests/modules/offer/application/test_offer_completion_golden.py` lockea `compute()` output (percentage + completed_sections + next_milestone + section_depth) para offer sintético por archetype.
- [ ] Todos los goldens pasan en HEAD pre-refactor.

### 05.B — Offer prompt renderer module

- [ ] `src/modules/sales_agent/application/services/offer_prompt_renderer.py` con `render_offer_prompt_lines(offer_data) -> list[str]`.
- [ ] Cada línea hardcoded de `agent_identity.j2` (offer body) tiene equivalente en este módulo.
- [ ] `agent_identity.j2`: offer body reemplazado por `{% for line in offer.prompt_lines %}{{ line }}\n{% endfor %}`.
- [ ] `knowledge_builder.build_identity` inyecta `prompt_lines` en cada offer dict antes de render.
- [ ] Golden agent_identity test sigue verde (byte-identical).

### 05.C — Data-driven inclusion

- [ ] Renderer consume `find_contract("offer", path)` por línea.
- [ ] `status != ACTIVE` → línea omitida.
- [ ] Arch test `test_offer_prompt_paths_subset_of_contract`: cada path en `OFFER_PROMPT_LINE_SPECS` pertenece al contract registry.
- [ ] Test: marcar field como DEPRECATED → desaparece del prompt sin tocar template.

### 05.D — Completion contract-driven

- [ ] `_SECTION_VALIDATORS` reemplazado por `_derive_section_validators_from_contract()`.
- [ ] Override `is_required_semantic=True` por field cubre TODO el conjunto previo de validators.
- [ ] Section→required-fields mapping derivado de `(contract.section, contract.is_required_semantic)`.
- [ ] Golden completion test sigue verde para cada archetype.
- [ ] Arch test `test_completion_required_fields_align_with_contract`.

### 05.E — Landing builders contract-aware

- [ ] Helper `_field_active("offer", path)` consume contract registry.
- [ ] Builders cubren paths via helper (silent skip si removed).
- [ ] Golden landing tests siguen verdes.
- [ ] Arch test `test_landing_builder_paths_subset_of_contract`: cada offer path leído por un builder pertenece al contract registry.

### 05.F — Tech debt

- [ ] Si pre-investigación encontró fields gap → contract extension commit.
- [ ] Si no → skip + nota en LEARNINGS.

### 05.G — Close

- [ ] `LEARNINGS.md` Fase 05 updated.
- [ ] `STATE.md` `active_phase: 06`, `last_green_commit` bumped.
- [ ] `STATUS.md` Fase 05 done, Fase 06 ready-to-start.
- [ ] `HANDOFF.md` actualizado con prompt Fase 06.

## Out-of-scope (FREEZE)

- Schemas FE — no se tocan.
- Brand/buyer migration — Fase 06/07.
- Copilot unification — Fase 08.
- Multi-channel projection — Fase 09.
- Refactor de `agent_identity.j2` brand block — Fase 06.
- Cambios a la lógica creativa de landing builders (copy decisions).
