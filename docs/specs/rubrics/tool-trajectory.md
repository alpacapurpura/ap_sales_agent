# Rubric — Tool Trajectory

```yaml
---
id: tool-trajectory
version: 1
applies_to: [agentic-story]
modules: [copilot, sales_agent]
threshold_default: 0.7
type: hybrid                                   # mix: code-based + LLM-judge
---
```

## Propósito

Verificar que el agente llama las tools correctas en orden razonable, sin tools forbidden, sin loops infinitos, sin tools innecesarias.

## Code-based assertions (deterministas)

### A1. Required tools llamadas

```python
all(tool in actual_tool_calls for tool in scenario.expected_tools)
```

- ✅ Pass: cada tool en `agentic_contract.expected_tools` aparece al menos 1 vez en trace
- ❌ Fail: missing tool

### A2. Forbidden tools NO llamadas

```python
not any(tool in actual_tool_calls for tool in scenario.forbidden_tools)
```

- ✅ Pass: ninguna tool de `forbidden_tools` fue llamada
- ❌ Fail: forbidden tool detected

### A3. Max calls respetado

```python
sum(1 for _ in actual_tool_calls) <= scenario.max_tool_calls_total
```

- ✅ Pass: total ≤ límite
- ❌ Fail: agent en loop o redundante

### A4. Sin loops obvios

```python
no_immediate_repeat(tool_calls)  # mismo tool con mismos args 2x seguidos
```

- ✅ Pass: tool A llamada con args X no se repite en pos N+1
- ❌ Fail: loop detection

## LLM-judge assertions (semánticas)

### A5. Order razonable

> Aunque `order_matters: false` en contrato, el judge evalúa si la secuencia tiene sentido para el goal.

- ✅ Pass: secuencia lógica (gather → reason → respond)
- ❌ Fail: agent llama action tool antes de read tool

### A6. Justificación implícita

> ¿Cada tool call tiene rationale en el thinking del agent?

- ✅ Pass: tool call precedida de razonamiento que la justifica
- ❌ Fail: tool call random sin contexto

### A7. Eficiencia

> ¿Usó N tools cuando podría haber resuelto con M < N?

- ✅ Pass: minimal viable tool set para responder
- ❌ Fail: redundancia (llama 3 read tools cuando 1 alcanza)

## Scoring

```
code_score = avg(A1..A4)
judge_score = avg(A5..A7)
final_score = 0.6 * code_score + 0.4 * judge_score
```

Threshold default: **0.7**.

## Auto-fail triggers

| Trigger | Score |
|---|---|
| Forbidden tool llamada | 0.0 |
| > 2x max_tool_calls | 0.0 |
| Loop detection (3+ same call same args) | 0.0 |

## Implementación grader

```python
def grade_tool_trajectory(trace, scenario):
    actual = [tc.name for tc in trace.tool_calls]

    # Code-based
    has_required = all(t in actual for t in scenario.expected_tools)
    no_forbidden = not any(t in actual for t in scenario.forbidden_tools)
    within_max = len(actual) <= scenario.max_tool_calls_total
    no_loops = no_immediate_repeat(trace.tool_calls)
    code_score = sum([has_required, no_forbidden, within_max, no_loops]) / 4

    # LLM judge for semantics
    judge_prompt = f"Evaluate tool trajectory:\nGoal: {scenario.goal}\nCalls: {trace.tool_calls}\n..."
    judge_score = llm_judge(judge_prompt)

    return 0.6 * code_score + 0.4 * judge_score
```

## Histórico

- v1 2026-05-04 — initial
