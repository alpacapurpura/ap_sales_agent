# Hot-fix Repro Mandatory

**Origen:** PI-12 S1 T-1.bis (2026-05-05). Handoff doc describió bug como
"`litellm.get_llm_provider()` raises BadRequestError → fallback needed in
cost_recorder.py". Si /dev-team spawneaba builder con esa diagnosis,
builder habría implementado fix incorrecto (provider fallback ya funciona
correctamente via try/except + hint). Real bug = test fixtures missing
`litellm_call_id` en mock response_metadata → `pop_cost(None)` returned
None → `cost_usd=None` → assertions failed.

Sin reproducción local pre-spawn, ~$8 USD wasted en builder Opus 4.7
implementando wrong scope.

## Regla cardinal

ANTES de spawn `builder-{backend|agentic|frontend}` para un hot-fix
ticket originado en handoff/incident doc/escalation, /dev-team
orchestrator (Claude Opus runtime) o `/po` redactor MUST reproducir la
falla localmente y validar el diagnóstico de scope antes de pasar al
builder.

## Cuándo aplica

Hot-fix ticket es cualquier ticket con AL MENOS UNA de estas señales:

- Ticket title o context contiene: `bug`, `hot-fix`, `regression`,
  `incident`, `bis`, `revert`, `fix forward`
- Ticket origin field menciona: `handoff doc`, `pase a producción failed`,
  `auditor escalation`, `customer report`
- Ticket spec describe symptom (no design from scratch) y propone
  scope quirúrgico (1-3 files, ≤2h estimate)
- Ticket sub-numero `T-N.bis` (per R8 sub-ticket convention)

## Workflow obligatorio

### Step 1 — Reproducción local

`/dev-team` (or `/po` cuando redacta spec) ejecuta el repro test/comando
citado en el handoff doc. Captura output verbatim:

```bash
# Per handoff doc T-1.bis:
cd backend && .venv/bin/pytest <repro test paths> -v --tb=short
# Output FAIL → confirma symptom existe
# Output PASS → handoff doc desactualizado, escalate
```

### Step 2 — Diagnóstico real

Compara symptom observado contra root cause propuesto en handoff:

- ✅ **Match:** symptom + traceback + log lines coinciden con causa
  propuesta → handoff diagnóstico VALIDADO. Proceed con scope handoff.
- ⚠️ **Mismatch:** symptom existe pero traceback apunta a código
  distinto del scope propuesto → handoff doc MISDIAGNOSED. STOP.
  - Document realización en T-{n}-impl-log.md sección "Diagnosis correction"
  - Re-redactar ticket spec con scope correcto
  - Spawn builder con scope corregido (NUNCA con scope handoff original
    si supiste mismatch)
- ❌ **No repro:** test no falla, comando no errora → handoff doc
  desactualizado o bug ya fixed por commit previo. STOP. Cierra ticket
  como `superseded` o escalate Chris.

### Step 3 — Cite repro evidence en spec/ticket

Ticket entry en `04-tickets.yaml` MUST incluir:

```yaml
repro_verified: true                                  # R26 — hotfix repro confirmed
repro_evidence:
  command: "cd backend && .venv/bin/pytest tests/X/test_y.py::test_z -v"
  output: |
    AssertionError: '>' not supported between NoneType and int
    at line 153 of test_y.py
  diagnosis_validates_handoff: false                  # if false, document correction
  diagnosis_correction: "Real cause is missing call_id bridge in mock fixture, NOT provider fallback as handoff suggested"
```

### Step 4 — Spawn builder

Builder spawn MUST cite `repro_verified: true` in prompt:

```
Agent({
  description: "Build hot-fix T-N",
  subagent_type: "builder-backend",
  prompt: "<pr_folder>: ...
           <ticket>: T-N (repro verified — see ticket.repro_evidence)
           ..."
})
```

Si `repro_verified: false` o ausente en hot-fix ticket → /dev-team
REFUSE spawn con mensaje:

```
ERROR — hot-fix ticket missing repro_verified per .claude/rules/hotfix-repro-mandatory.md.
Run repro command first, document evidence, set repro_verified: true.
```

## Anti-patterns prohibidos

- ❌ Builder spawn con scope tomado de handoff doc sin reproducción local
- ❌ Repro reportado en ticket pero diagnosis_correction omitida cuando
  symptom y handoff causa diverge
- ❌ Spec ratifica handoff diagnosis sin citar repro evidence verbatim
- ❌ Hot-fix ticket sin `repro_verified` field

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 /po SKILL | Step "Reproducción local" obligatorio cuando redacta spec hot-fix | `/po` |
| 2 /dev-team SKILL | Step 0.5 "Verify repro_verified" antes spawn builder | `/dev-team` |
| 3 04-tickets template | `repro_verified: bool` field documentado para hot-fix tickets | template |
| 4 Auditor REVIEW | Cat 11 (cross-cutting) verifica repro_verified citado en hot-fix | auditors |
| 5 Builder agent | Prompt header check: `repro_verified: true` o magic ack | builder-* agents |

## Caso origen detallado

PI-12 S1 T-1.bis (2026-05-05):

**Handoff doc decía:**
> Bug: `litellm.get_llm_provider("kimi/kimi-k2.6")` raises BadRequestError.
> Fix: en cost_recorder.py, si get_llm_provider() raises → fallback
> provider = model.split('/')[0].lower() if '/' in model else 'unknown'.

**Repro local mostró:**
```
cost_recorder.unknown_provider error_class=BadRequestError hint=kimi model=kimi-k2.6  ← OK, hint fallback works
cost_recorder.no_call_id_on_response model=kimi-k2.6 provider=kimi                     ← real bug here
TypeError: '>' not supported between NoneType and int                                  ← assertion fail
```

**Diagnosis correction:** provider fallback ya funciona (try/except + hint
already in `_canonical_provider`). Real symptom es `_extract_litellm_call_id`
returning None porque mock fixture sin `litellm_call_id` en
`response_metadata`. Fix = test bridge migration, NO production code.

Sin Step 1-2 obligatorios habríamos shipped cambio incorrecto a
cost_recorder.py + tests still failing. Con repro mandatory, scope se
redirigió a tests/conftest.py + 2 test files migration.

## Referencias

- `docs/process/process-improvement-handoff-2026-05-05.md` (caso origen handoff doc misdiagnosis)
- `docs/process/learnings.md` 2026-05-05 entry — T-1.bis closure
- `.claude/skills/dev-team/SKILL.md` Step 0.5 (R26 enforcement)
- `.claude/skills/po/SKILL.md` Step "Reproducción local" (R26 enforcement)
- `docs/specs/templates/04-tickets-template.yaml` § repro_verified
