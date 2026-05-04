# 01-spec.md — Template (PO)

> Owner: `/po`. **Spec ejecutable Gherkin AI-resistant.** Esta es la fuente de verdad de QUÉ debe construirse.
> Los architect, dev y auditor consumen ESTE archivo + el story YAML.
> Los scenarios de aquí se reflejan 1:1 en el story YAML (`docs/product/stories/{m}/{story-id}.yaml`).

---
story_id: STORY_ID_KEBAB
type: ui-story | agentic-story | service-story
module: MODULE_NAME
capability: CAPABILITY_ID
po_version: 1                                     # bump cuando cambies post-handoff
last_modified: 2026-05-04T14:30Z
ratified_by_chris: false                          # /po pide ratificación antes pasar a UX/architect
links:
  story_yaml: "../../../../../product/stories/{module}/{story-id}.yaml"
  story_md: "00-story.md"
---

## Resumen ejecutivo

[1 párrafo: qué se construye, para quién, outcome esperado.]

## Acceptance Criteria (Gherkin AI-resistant)

> Mínimo 4 scenarios: 1 happy + 1 negative + 1 edge + 1 adversarial.
> Cada scenario es testeable + tiene grader explícito.

### Scenario 1 — `happy-path` (`type: happy`)

**Given:**
- [precondición concreta y verificable]

**When:**
- [acción exacta del actor]

**Then:**
- [efecto 1 medible]
- [efecto 2 medible]
- [efecto 3 medible]

**Graders:**
- [Tipo grader] — [target/path]

---

### Scenario 2 — `[id-negative]` (`type: negative`)

**Given:** ...
**When:** [input/estado inválido]
**Then:**
- [error visible/respuesta clara]
- [estado NO se modifica]
- [audit log entry si aplica]

**Graders:** ...

---

### Scenario 3 — `[id-edge]` (`type: edge`)

**Given:** [estado de borde: concurrencia, límite, race condition]
**When:** ...
**Then:** ...

**Graders:** ...

---

### Scenario 4 — `[id-adversarial]` (`type: adversarial`)

> AI-resistant: usuario hostil, tenant cross-leak, prompt injection, datos sensibles.

**Given:** ...
**When:** [acción adversarial]
**Then:**
- [security/safety check explícito]
- [no leak]
- [audit/alerting]

**Graders:** ...

---

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Latencia | p95 < N ms | métrica + load test |
| Cost | <= $X/session (agentic) | copilot_llm_call |
| Mobile | viewport >= 375px (ui) | Playwright resize |
| Accesibilidad | WCAG AA (ui) | axe-core |
| i18n | Spanish neutro (no voseo, salvo sales_agent voz tenant) | Lint regex |
| PII | Response no expone PII sin mask | response_model Pydantic |
| Tenant isolation | Tenant cross → 403/404 | adversarial scenario |

## Constraints técnicos heredados

- [De `.claude/rules/*` que aplican: backend-ddd, tenant-isolation, etc.]
- [Tessl skills relevantes a citar: tessl__fastapi, tessl__zod, ...]

## Cross-module impact

- **Lee de:** [módulos cuyas tablas/eventos consume]
- **Es leído por:** [módulos que dependen]
- **Eventos emitidos:** [event_name v1]
- **Eventos consumidos:** [event_name v1]

## Open questions (para resolver con Chris ANTES de UX/architect)

- [ ] [Pregunta 1]
- [ ] [Pregunta 2]

## Próximo paso

- Si `type=ui-story` → `/ux-ui` lee `01-spec.md` → produce `02-design-ui.md`
- Si `type=agentic-story` → `/ux-agentico` lee `01-spec.md` → produce `02-design-agentic.md`
- Si `type=service-story` → skip UX → `/architect` directo

## Changelog

- v1 2026-05-04 — /po draft inicial
- v2 2026-05-04 — Chris ratificó scenarios 2 y 3, ajusté wording scenario 4
