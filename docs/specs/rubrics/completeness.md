# Rubric — Completeness

```yaml
---
id: completeness
version: 1
applies_to: [agentic-story, service-story]
threshold_default: 0.75
---
```

## Propósito

Verificar que la respuesta/output del agente cubre TODOS los criterios pedidos por el user/contrato, sin omitir partes críticas.

## Inputs al juez

- `user_request` — qué pidió el user
- `agent_response` — qué entregó
- `expected_components` — lista de componentes que debe contener (de scenario `then:`)

## Assertions

### A1. Cubre cada componente esperado

- ✅ Pass: cada item de `expected_components` aparece en response
- ❌ Fail: 1+ componente missing

### A2. No omite por simplicidad

- ❌ Fail: agent omite parte difícil ("el resto te lo cuento más tarde")
- ✅ Pass: aborda todo o explícitamente split en próximos turns

### A3. Prioriza por importancia

> Para outputs de auditoría/análisis (brand-audit, offer-audit), gaps deben aparecer ordenados por sales-impact, no alfabético/random.

- ✅ Pass: items priorizados con criterio explícito
- ❌ Fail: orden arbitrario

### A4. Cada item con acción concreta

> Especialmente en outputs de tipo "qué hacer ahora".

- ✅ Pass: cada gap/issue tiene 1+ acción accionable
- ❌ Fail: solo descripción sin "qué hacer"

### A5. Sin redundancias

- ✅ Pass: cada componente aparece 1x
- ❌ Fail: misma idea repetida 3 veces con diferentes palabras

### A6. Closure

- ✅ Pass: response termina con próximo paso claro o pregunta abierta
- ❌ Fail: response termina abrupto, no clear next step

## Scoring

```
score = passed_assertions / total
```

Threshold default: **0.75**.

## Customización per scenario

Cada scenario en story YAML define en `graders[].assertions[]` los criterios específicos:

```yaml
- type: llm_rubric
  rubric: ../../../specs/rubrics/completeness.md
  assertions:
    - "Identifica buyer_personas como gap"
    - "Identifica testimonials como gap"
    - "Prioriza por sales-impact"
    - "Cada gap tiene 1+ acción"
    - "No menciona campos que no existen en brand schema"
  threshold: 0.8
```

El judge evalúa cada assertion de la lista contra el response, retorna score = passed / total.

## Histórico

- v1 2026-05-04 — initial
