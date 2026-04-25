# Fase 09 — Multi-channel projection · SPEC

## Objetivo

Promover el `FieldContract` a contract conversacional channel-agnostic.
El copilot consume un algoritmo determinístico `next_question(module,
state)` que elige el siguiente field a preguntar usando la metadata
del contract. Adapters web (form-runtime guided) y chat (whatsapp /
telegram via stub adapter) ejercitan el mismo algoritmo. Wiring real
copilot↔chat queda fuera de scope (futuro sprint).

## Diseño

### Algoritmo `next_question`

```python
# copilot/application/orchestrator/conversational_questioning.py

def next_question(
    module: str,
    state: Mapping[str, Any],
    *,
    section: str | None = None,
) -> FieldContract | None:
    """Pick next field to ask for in `module`.

    Channel-agnostic. Caller decides how to render the contract.

    Selection:
        - status == ACTIVE
        - can_propose == True
        - is_required_semantic == True (preferential)
        - missing in `state` (None / "" / [] / {})
        - gate satisfied (gate is None or state[gate] non-empty)
        - section filter (if provided)

    Order:
        - Required-missing before optional-missing.
        - Within group: section_order (alphabetic stable), -priority, path.
    """
```

Returns `None` cuando no hay candidate (módulo completo).

### Helpers

- `_get_path(state, path) -> Any | None` — resuelve dotted-path. List items
  retornados como list. Empty list/dict = missing.
- `_is_missing(value) -> bool` — None / "" / [] / {} = missing.
- `_gate_satisfied(gate: str | None, state: Mapping) -> bool` — None gate
  always True; populated → check non-empty.

### Render contract

Caller decide. Two reference adapters:

**Web (guided advance)**:
```python
contract = next_question("offer", offer_state)
if contract:
    hint = contract.human_question_es or _humanize(contract.path)
    return {"suggested_field_path": contract.path, "hint": hint}
```

**Chat stub (E2E test)**:
```python
contract = next_question("brand", brand_state)
adapter.send(contract.human_question_es or _humanize(contract.path))
```

### Adapter port

```python
# shared/links/ports/conversational_channel.py

class ConversationalChannelPort(ABC):
    """Abstract sink for conversational questioning output."""

    @abstractmethod
    async def ask(self, contract: FieldContract, *, context: dict | None = None) -> None:
        """Emit the question to the user via this channel."""
```

Implementations:
- `WebGuidedChannel` — appends suggestion to advance_guided_setup payload.
- `InMemoryChannel` — captures outbound asks for E2E tests.
- (futuro) `WhatsappChannel`, `TelegramChannel` — wrap existing adapters.

## Sub-fases

| Sub-paso | Descripción | Files | Commit |
|---|---|---|---|
| 09.A | docs (este commit): PRE_INVESTIGATION + SPEC + ACCEPTANCE | docs/refactors/.../phases/09/* | (a) |
| 09.B | `next_question` core + unit tests | copilot/application/orchestrator/conversational_questioning.py + tests/modules/copilot/test_conversational_questioning.py | (b) |
| 09.C | Web integration (guided advance enrichment) | copilot/application/tools/guided/advance.py + tests | (c) |
| 09.D | Channel adapter port + in-memory adapter + tests | shared/links/ports/conversational_channel.py + copilot/infrastructure/channels/* + tests | (d) |
| 09.E | E2E channel-agnostic (web stub + chat stub) | tests/modules/copilot/test_conversational_e2e.py | (e) |
| 09.F | `human_question_es` enrichment top required fields | offer/brand/buyer overrides | (f) |
| 09.G | LEARNINGS + STATE bump + HANDOFF (cierre fase / refactor) | STATE.md + LEARNINGS.md + STATUS.md + HANDOFF.md | (g) |

Cada commit revertible. 09.B es el core; si 09.C-F sufren regresión,
revertir esos commits sin tocar 09.B.

## Decisiones de diseño

1. **Algoritmo puro, no LLM**: `next_question` retorna `FieldContract`
   determinístico. LLM-driven naturalness vive en el adapter, no en el
   selector. Razón: testability + reproducibility.
2. **Field-level, no block-level**: `block_generator.py` sigue
   funcionando para top-level navigation. `next_question` profundiza
   adentro del bloque cuando se llama con `section=block.id`.
3. **Gate dependencies son one-shot, no DAG**: per ADR-014, `gate: str`
   apunta a UN path precondición. No hay multi-gate ni AND/OR. Si
   semánticamente se necesita, futura ADR.
4. **Missing detection**: empty list `[]`, empty dict `{}`, blank string
   `""`, None — todos cuentan como missing. Booleanos `False` NO son
   missing (false ≠ ausente).
5. **Required-first ordering**: candidates con `is_required_semantic=True`
   ganan prioridad sobre opcionales. Dentro del subset: `(section,
   -priority, path)` (priority alta gana, tie-break lex).
6. **Status filter**: solo `ACTIVE`. Deprecated/Removed nunca se ofrecen.
7. **Channel adapter port**: abstract en `shared/`. Concrete in-memory
   adapter en `copilot/infrastructure/channels/`. Real
   whatsapp/telegram bridge OUT of scope; reusan `BaseChannel` cuando
   se construya el wiring copilot↔channel.

## Out of scope

- Wiring real copilot ↔ whatsapp/telegram (requiere copilot orchestrator
  channel-aware + tenant-owner identity en webhook). Sub-fase futura
  o sprint product-level.
- `redo_if_changes` invalidation. Documentado en contract pero sin
  state manager que lo honre.
- LLM-driven question reformulation. Caller adapter puede hacerlo,
  pero no es parte del algoritmo.
- Schema FE changes (INVARIANT 9).
- Multi-gate (AND/OR) o DAG dependencies.
- Diferidos Fase 05/07 (NO tomar este sprint).

## Riesgo

**Alto** declarado per PLAN. Mitigaciones:

- Algoritmo pure-function = trivialmente testeable + revertible.
- Web integration adicional, no replace (legacy block flow sigue
  intacto).
- Adapter port en `shared/` separa concerns.
- Sub-fases atómicas; cada una revertible sin tocar las otras.

## DoD (Definition of Done)

Ver `ACCEPTANCE.md` per sub-paso.

## Reglas inquebrantables

- INVARIANTS 1-20 todos aplican.
- TDD: test antes que impl en cada sub-paso (B/C/D/E).
- Spanish neutro LATAM en `human_question_es` (09.F).
- UX byte-identical: web copilot guided sigue funcionando idéntico
  cuando algoritmo retorna None (fallback al flow legacy).
- No reabrir Fases 04-08.
- Stage por nombre. No `git add -A`.
