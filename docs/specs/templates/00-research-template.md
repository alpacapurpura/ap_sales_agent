# 00-research-template.md — Research deep (state=idea)

> **OPCIONAL.** Solo para ideas grandes (>5d trabajo estimado, novedad, alto riesgo, o impacto cross-módulo). Ideas pequeñas pueden saltar directo a refining.
>
> **Owner:** Chris + `/pm`. NO `/po` (research es pre-spec, no spec).
>
> **Estado de la story:** `idea` (post research puede dropear, parkear o promover a `refining`).
>
> **Output:** Este archivo lo lee Chris para decidir si vale refinarla. NO se ejecuta automáticamente. Puede iterarse N veces.

---
story_id: STORY_ID
state: idea
created: YYYY-MM-DD
researcher: chris + /pm
last_modified: YYYY-MM-DD
research_iterations: 1
decision_pending: true
decision_options: ["refining", "parked", "dropped"]
---

# Research — {Tema corto descriptivo}

## 1. Problema / Oportunidad

> ¿Qué dolor del user resuelve? ¿Qué KPI/outcome de negocio mueve? Sin tecnología.

- Dolor user: ...
- KPI movido: ...
- Outcome conectado: ...

## 2. Lo que hacen otros — Competitive analysis

> Min 3 competidores. Indagar UX flows + pricing + moat.

| Competidor | Producto | Cómo lo resuelve | Pros | Cons | Pricing |
|---|---|---|---|---|---|
| HubSpot | Smart CRM | ... | ... | ... | $$$ |
| ActiveCampaign | Marketing automation | ... | ... | ... | $$ |
| Intercom | Conversational | ... | ... | ... | $$$$ |

**Moats que encontramos:**
- ...
- ...

**Gap percibido (lo que NO hacen bien):**
- ...

## 3. Viabilidad técnica

### Stack actual relevante

- Módulos involucrados: `brand`, `offer`, `copilot`, ...
- Capabilities afectadas: lista
- Dependencias externas nuevas: API X, librería Y, servicio Z

### Gaps técnicos a resolver

- [ ] Gap 1
- [ ] Gap 2

### Riesgos técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Latencia LLM > 10s | Media | Alto | Streaming + cache prompt |
| Multitenant cross-leak | Baja | Crítico | Reusar `tenant_id` filter |

## 4. Costo estimado

### Build (one-time)

- Dev effort: X dev-days (split BE/FE/agentic)
- Diseño UX/agentic: Y horas Opus
- Architect package: Z horas Opus

### Runtime (recurring)

| Componente | USD/mes/tenant | USD/mes 1000 tenants |
|---|---|---|
| LLM tokens (provider X) | 0.50 | 500 |
| Infra (Postgres+Redis+Qdrant adicional) | 0.10 | 100 |
| External API calls | 0.20 | 200 |
| **Total runtime** | **0.80** | **800** |

### Break-even analysis

> ¿Cuántos tenants activos necesitamos para que la feature pague su runtime?

## 5. Cómo podríamos hacerlo nosotros (mejor que competidores)

### Hipótesis driver

- **H1:** Diferenciamos en X porque ...
- **H2:** Aprovechamos Y de Nicolify (multitenant + voice fidelity) ...
- **H3:** Iteramos faster porque ...

### Propuesta(s) de solución

#### Opción A — minimalista
- Scope: ...
- Tradeoff: ...
- Estimado: 3 dev-days

#### Opción B — completa
- Scope: ...
- Tradeoff: ...
- Estimado: 8 dev-days

#### Opción C — disruptiva
- Scope: ...
- Tradeoff: novedad alta, riesgo alto
- Estimado: 12 dev-days

## 6. Mockups / Prototipos

> Inline HTML / ASCII / screenshots. Si HTML separado → `mockups/{story-id}/index.html`.

### Mockup A (concepto)

```
┌──────────────────────────────────┐
│  [Header con búsqueda]           │
├──────────────────────────────────┤
│  Cards grid                      │
│  □ Item 1   □ Item 2   □ Item 3  │
└──────────────────────────────────┘
```

### Mockup B (alternativa)

```html
<!-- inline mockup HTML -->
```

## 7. Sources / referencias externas

> Web research links, papers, blog posts, competitor screenshots — todo lo que sustente decisiones arriba.

- [Source 1 título](https://example.com/1)
- [Source 2 título](https://example.com/2)
- [Internal: docs/process/learnings.md § X](#)

## 8. Decisión pendiente

- [ ] **Refinar** (state=idea → refining): Chris triggers "refinemos", spec escrita por `/po-ux` o `/po`
- [ ] **Park** (state=parked): no priority ahora, revisitar en N meses
- [ ] **Drop** (state=dropped): won't do — razón:

## 9. Bitácora

- {YYYY-MM-DD} — Research v1: research initial. Encontramos ...
- {YYYY-MM-DD} — Research v2: profundizamos competidor X. Cambia hipótesis ...
- {YYYY-MM-DD} — Chris decide: {refinar | park | drop}.
