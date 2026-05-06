# PR-{N}-{slug} — {Título}

> Product Requirement. Entregable handoff. Lo lee `/ux-flow-architect` y luego implementadores.

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-{N}-{slug} |
| PI padre | PI-{M}-{theme} |
| Estado | discovery / drafting / ready / handoff / building / shipped / closed |
| Owner PM | /pm |
| Fecha creación | {YYYY-MM-DD} |
| Última edición | {YYYY-MM-DD} |
| Opportunity origen | `opportunities/{slug}.md` (link, opcional) |

## Contexto

¿Por qué ahora? 2-3 frases. Origen: dolor user observado / oportunidad detectada / restricción negocio.

## Job-to-be-Done

> Cuando {situación}, quiero {motivación}, para que {resultado esperado}.

Una frase. Job real, no feature description.

## Outcome esperado (medible)

- Métrica cuantitativa: {ej: 80% setup completo en <10min} 
- Métrica cualitativa: {ej: user dice "esto resuelve mi dolor"}

## Usuario

- Persona target: {creador / infoproductor / negocio experto / todos}
- Etapa lifecycle: {onboarding / activación / retención / expansion}
- Canal entrada: {copilot / studio UI / email / etc}

## Solución propuesta

### Walking skeleton (MVP)

Mínimo end-to-end funcional. Bullets:
- Capacidad 1
- Capacidad 2
- Capacidad 3

### Out of scope (explícito)

- Cosa que NO va — y por qué
- Cosa que NO va — y por qué

### Capacidades opcionales (si tiempo)

- Capacidad nice-to-have

## User stories

Formato: `Como {actor}, quiero {acción}, para {beneficio}.`

1. Como {...}, quiero {...}, para {...}.
   - Criterios aceptación:
     - Dado {contexto}, cuando {acción}, entonces {resultado}.
2. ...

## Operable desde copilot? **(obligatorio)**

- [ ] **Sí** — descripción flujo conversacional:
  ```
  User: "{frase ejemplo}"
  Copilot: {respuesta + tool ejecución}
  ```
- [ ] **No** — justificación robusta:
  - {por qué la UI directa es necesaria y el flujo conversacional no aporta}

Default = Sí. No requiere argumento robusto sobre por qué la conversación no es suficiente.

## Restricciones negocio

- Multitenant: ✅ aislamiento `tenant_id`
- LATAM neutro: ✅ tuteo, sin voseo
- Currency/timezone: {N/A | usa TenantLocale}
- PII: {N/A | response_model + masking}
- Conectores externos requeridos: {Meta / Shopify / etc / ninguno}

## Dependencias

- Módulos backend tocados: {brand / offer / sales_agent / ...}
- Módulos frontend tocados: {features/...}
- Nuevas integraciones externas: {OAuth nuevo / webhook nuevo / ninguna}
- PRs bloqueantes: {PR-X | ninguno}

## Decisiones tomadas

ADR-style. Append-only. Fecha + decisión + razón.

| Fecha | Decisión | Razón |
|---|---|---|
| {YYYY-MM-DD} | {qué se decidió} | {por qué} |

## Decisiones diferidas

Puntos NO resueltos hoy. Documentados para futuro PI o PR follow-up.

- {pregunta abierta}
- {pregunta abierta}

## Research relevante

Links research files que informaron decisiones:
- `research/{date}-{slug}.md` — {1 frase qué aporta}

## Inspiración / "Robar como artista"

Productos / startups / patrones que estudiamos. Qué tomamos, qué no:
- **{Producto X}**: tomamos {patrón}. No tomamos {patrón}.

## Handoff a UX

Cuando estado = `ready`, este PR es input para `/ux-flow-architect`.

PM dice a Chris: "PR-{N} listo. Invocá `/ux-flow-architect` con prompt: 'Diseñar UX para `docs/pm-nico/pis/PI-{M}/prs/PR-{N}-{slug}.md`'."

## Cambios post-handoff

Si UX o builder detecta gap funcional, vuelven al PM (no autodefinen). PM evalúa, decide, registra en "Decisiones tomadas".

## Cierre

Cuando shipped:
- Estado = `shipped`
- Update `current-state/{module}.md` correspondiente
- Si lección reusable → migrar a `roadmap.md` retro o `pis/PI-{M}/retro.md`
