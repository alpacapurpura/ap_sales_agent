# Pre-investigación obligatoria — Fase 09

## Sección 1 — Estado infra channel

**Q1.1** — ¿Whatsapp/telegram channels integrados ya?

Si no → bloqueante. Esta fase asume infra existe. Ajustar scope si
no.

## Sección 2 — Trade-off algoritmo vs LLM

**Q2.1** — ¿El algoritmo decide TODO o LLM tiene grados de libertad?

Híbrido natural:
- Algoritmo selecciona candidate fields (filtra gate/missing/status).
- LLM decide orden y formula la pregunta natural usando `human_question_es`
  como base.

Documentar decisión.

## Sección 3 — Web compatibility

**Q3.1** — ¿La web sigue usando form-runtime o adopta `next_question`?

Decisión: form-runtime sigue. `next_question` es para canales no-web.
Eventualmente web puede ofrecer modo "guiado" que use el mismo algoritmo.

## Sección 4 — Tests E2E disponibles

**Q4.1** — ¿Hay infraestructura E2E para chat?

Output

- [ ] Estado infra channel confirmado.
- [ ] Decisión algoritmo vs LLM.
- [ ] Compat web confirmada.
- [ ] Tests E2E plan.
