# Rubric — Voice Fidelity

```yaml
---
id: voice-fidelity
version: 1
applies_to: [agentic-story]
modules: [sales_agent, copilot]
threshold_default: 0.8                         # score 0.0-1.0
ssot:
  - "personality_profiles.system_instruction (per-tenant)"
  - ".claude/rules/sales-agent-brand-voice.md"
---
```

## Propósito

Verificar que la respuesta del agente respeta la voz definida por el tenant en su `PersonalityProfile.system_instruction` (compiler v2, 6 bloques "ASÍ HABLAS / ASÍ NO"). NO mide buena escritura — mide fidelidad al perfil.

## Inputs al juez (LLM-as-judge)

- `tenant_voice_profile` — extraído de `PersonalityProfile.system_instruction` para el tenant del trial
- `agent_response` — respuesta del agente bajo evaluación
- `previous_turns` — context de turnos previos en la conversación

## Assertions (cada una pondera igual, score promediado)

### A1. Vocabulary alignment

¿La respuesta usa palabras y frases del registro del tenant?
- ✅ Pass: usa términos del bloque "ASÍ HABLAS" + evita los del bloque "ASÍ NO"
- ❌ Fail: usa palabras genéricas tipo "estimado cliente" cuando tenant es informal directo

### A2. Tone match

¿El tono coincide?
- Tonos posibles: `formal-cálido | informal-directo | técnico-profesional | empático-paciente | enérgico-motivador | sobrio-informativo`
- ✅ Pass: tono del response es el declarado en perfil
- ❌ Fail: tenant declara "informal-directo" y agente responde con tono "formal-cálido"

### A3. Voseo respeto (si tenant es AR/UY)

- Si `tenant.country IN [AR, UY]` y perfil dice voseo → response usa voseo (`tenés`, `podés`, `mirá`)
- Si `tenant.country IN [MX, CO, PE, CL, EC, ES]` → response usa tuteo (`tienes`, `puedes`, `mira`)
- ❌ Fail: voseo en tenant tuteo o viceversa

### A4. Emoji policy

- ✅ Pass: respeta declaración del perfil (uso o NO de emojis)
- ❌ Fail: agente usa emojis cuando perfil dice NO

### A5. Length / cadence

- ✅ Pass: longitud de mensaje match patrón típico tenant (corto/medio/largo)
- ❌ Fail: tenant declara "respuestas cortas" y agente escribe párrafos largos

### A6. Sin metáforas prohibidas

- ✅ Pass: no usa metáforas / muletillas listadas en bloque "ASÍ NO"
- ❌ Fail: agente usa "vamos a romperla" cuando perfil prohíbe lenguaje deportivo

### A7. Apertura/cierre apropiado

- ✅ Pass: opening + closing match estilo tenant
- ❌ Fail: tenant es directo sin saludos largos, agente responde con "¡Hola, mi querido cliente!"

## Scoring

```
score = sum(assertions_passed) / len(assertions)
```

Threshold default: 0.8 (pasa al menos 6 de 7).

## Anti-pattern detector

> Antes de evaluar, ejecutar regex check rápido. Cualquier match = score auto < 0.5:

| Pattern | Cuándo es violación |
|---|---|
| "Estimado cliente" / "Apreciado usuario" | tenant informal |
| "Ojalá" / "Quizás" / "Tal vez" | tenant declara estilo "asertivo-directo" |
| "Mi rey" / "Mi reina" / "Querido/a" | tenants profesionales |
| "Como inteligencia artificial..." | NUNCA — agente jamás declara ser IA en respuestas |
| "Mi sistema dice" / "Mis instrucciones" | NUNCA — leak de internals |

## Calibración con humano

Cada 3 meses: 50 transcripts + 2 expertos humanos. Si LLM-judge agrement < 80% con humanos → re-prompt el judge o ajustar threshold.

## Histórico

- v1 2026-05-04 — initial rubric basado en compiler v2 sales_agent
