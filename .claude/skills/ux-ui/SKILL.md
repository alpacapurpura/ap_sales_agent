---
name: ux-ui-deprecated
description: "DEPRECATED skill (post pm-redesign 2026-05-06 Wave 3). Replaced by /po-ux fusión for UI standard stories (CRUD/list/detail/form/dashboard). For novel/disruptive UI use /ux-disruptivo (7-fase Design Thinking). For agentic conversational flows use /ux-agentico. NEVER invoke this skill — it is kept only for historical reference of legacy paradigm where 01-spec.md (PO) and 02-design-ui.md (UX) were separate artifacts. The fusion (/po-ux) is more efficient because Nicolify UI std uses constrained design system (Tailwind tokens + Shadcn primitives + FSD-Lite) where separating spec/design produced 60% redundant content."
allowed-tools: Read
model: opus
---

# /ux-ui — DEPRECATED (Wave 3 pm-redesign 2026-05-06)

> **🛑 DEPRECATED.** Do NOT invoke this skill.
>
> **Replaced by:**
> - `/po-ux` (fusión `/po` + `/ux-ui`) for **UI standard stories** (CRUD/list/detail/form/dashboard)
> - `/ux-disruptivo` for **novel UI** (7-fase Design Thinking workflow)
> - `/ux-agentico` for **agentic conversational flows** (state machine + slot architecture)
>
> **Why deprecated:** UI std in Nicolify uses constrained design system (Tailwind tokens + Shadcn primitives + FSD-Lite). Separating `01-spec.md` (PO) and `02-design-ui.md` (UX) produced 2 docs with ~60% solapamiento (microcopy duplicado, estados duplicados, scenarios verificando estados visuales separados de Gherkin). Wave 3 pm-redesign (2026-05-06) fused both into `/po-ux` producing single `01-spec.md` UNIFICADO.
>
> **For history:** legacy content of this skill preserved below for reference. Active workflow → use `/po-ux`.

## Decision matrix (which skill to use instead)

| Tipo story | Skill replacement |
|---|---|
| **UI standard** (CRUD/list/detail/form/dashboard reusable Shadcn primitives) | **`/po-ux` (NEW fusión)** |
| **UI mixed** (UI std + tool calls agentic) | `/po-ux` para spec + sección agentic-handoff → `/ux-agentico` para flow |
| **UI disruptiva/novel** (paradigma visual nuevo, no Shadcn pattern) | `/ux-disruptivo` 7-fase → `/po` formaliza spec |
| **Cross-feature navigation audit** | `/ux-flow-architect` → outputs UI-SPEC para `/po-ux` formalizar |
| **Agentic conversational flow** | `/ux-agentico` (state machine + voice + eval pass^k) |

## Legacy reference (DO NOT invoke)

> The original ux-ui skill produced `02-design-ui.md` separately from `01-spec.md` (PO output). This created friction: changes needed 2-file coordination, microcopy/estados duplicated. New `/po-ux` fusion writes ONE artifact with Gherkin + wireframes inline + estados + microcopy + graders.

Owner: ~`02-design-ui.md`~ → now `01-spec.md` UNIFICADO via `/po-ux`.

## Inputs obligatorios

1. `01-spec.md` — entrada SSoT. Tu mockup debe reflejar 100% scenarios.
2. `docs/product/stories/{m}/{id}.yaml` — story header
3. `00-story.md` — para entender contexto / out of scope
4. `docs/product/modules/{m}.md` — UI existente módulo (no duplicar)
5. `frontend/src/app/...` y `frontend/src/features/...` — patterns reales repo
6. `frontend/src/components/ui/` — Shadcn primitives DISPONIBLES (no inventar)
7. `tailwind.config.*` / `globals.css` — design tokens proyecto

## Skills cargados (HARD GATE)

ANTES de mockup:
- `frontend-expert` — FSD-Lite, Tailwind tokens, Shadcn primitives reuse
- `tessl__shadcn-ui` — component selection, customisation
- `tessl__tailwind` — semantic tokens, no hardcoded hex
- Domain skill según módulo (`brand-expert`, `offer-expert`, `metrics-expert`, etc.)
- `chrome-devtools-verify` (para verify post-design en dev-app)

## Workflow

### Step 1 — Validar scope

Leer `01-spec.md` + `00-story.md` + capability YAML. Captura:
- Scenarios (qué se construye)
- Out-of-scope explícito (qué NO se construye)
- Constraints (mobile, latency, accessibility)

Si scope poco claro → escala /po: "01-spec.md tiene scope ambiguo en X. Refiná antes de UX."

### Step 2 — Mockup HTML primer draft

`mockups/{screen-name}.html` por pantalla. Reglas:

1. **1 archivo HTML por pantalla.** Si flow multi-step → `index.html` linkea entre ellos.
2. **Stack visual MUST match Nicolify:**
   - Tailwind utility classes (no inline `style=`)
   - Shadcn primitives (CDN o equivalente Tailwind)
   - Lucide icons via CDN
   - Design tokens del proyecto (no hex literal)
3. **Realistic data LATAM** (no Lorem ipsum, no "John Doe", no `test@test.com`)
4. **Spanish neutro LatAm** TODAS strings
5. **Responsive:** desktop + tablet + mobile sections en mockup
6. **Accessibility hints visibles:** ARIA labels, focus states, contrast adequado

Server preview opcional:
```bash
cd <story_folder>/mockups && python3 -m http.server 8888
```

Output al user:
```
Mockup screens: {lista}
URL local: http://localhost:8888/{screen}.html
Design decisions clave:
- Layout: {paradigma — drawer/modal/page}
- Componentes: {Shadcn list}
- Tokens: {bg-card, text-muted-foreground, ...}

¿Qué te parece? Decime qué cambiar.
```

### Step 3 — Iterar con Chris

**NUNCA rebuilds from scratch.** Solo `Edit` archivo existente. Cambios incrementales.

| Feedback Chris | Acción |
|---|---|
| Cambio dentro scope | Aplicar + resumir "qué cambié + por qué" |
| Cambio FUERA scope | STOP. Escala /po o /pm: "user pidió X out-of-scope. Decisión necesaria." |
| Hardcodear color violando design system | Proponer alternativa con tokens semánticos |
| Componente que no existe en `components/ui/` | Si scope permite: flag para builder ("crear shared/data-table"). Si no: workaround con primitives existentes. |

Cada iteración termina:
```
Mockup actualizado. Cambios: {lista}.
¿Más cambios o sigo a 02-design-ui.md?
```

Loop hasta Chris dice "está bien" / "perfecto".

### Step 4 — Producir 02-design-ui.md

Seguir template `docs/specs/templates/02-design-ui-template.md`. Llenar:
- Información architecture (ruta, sidebar, modal vs page)
- Layout + wireframe ASCII o link mockup HTML
- Componentes (reutilizados vs nuevos, con paths)
- Estados UI (idle/loading/success/error/empty) con qué muestra cada uno
- Data flow (RHF/Zod/React Query/fetchClient/invalidate)
- Responsive breakpoints
- Accessibility (ARIA, keyboard, focus, contrast)
- Microcopy Spanish neutro tabla
- Telemetría / events
- Brand voice
- Spec deltas (si UX descubrió edge cases nuevos)

### Step 5 — Spec deltas (si aplica)

Si durante diseño descubriste:
- Edge case que `01-spec.md` no cubre
- Estado UI no documentado
- Constraint que no estaba

Escribí en `02-design-ui.md` § Spec deltas + crea `delta-spec.md` separado:
```
[delta-spec.md]
Story: {id}
UX detectó:
1. Estado X no cubierto por scenario actual
2. Edge case Y...
Propongo agregar scenario Z al 01-spec.md.
@po: ratificar.
```

`/po` lee delta → decide aceptar/rechazar → ratifica → bump `po_version`.

### Step 6 — Hand off

```
UX done.
Deliverables:
- 02-design-ui.md (component contracts + responsive + interactions + Spanish strings + tokens)
- mockups/{N}.html ({lista})
- delta-spec.md (si aplica)

Próximo: /architect lee 01+02 → spawn /architect-{be,fe} → produce 03-arch + 04-tickets.yaml.

¿Invoco /architect ahora o lo hacés vos?
```

Update checkpoint:
```yaml
phase: UX_UI → ARCHITECT
last_artifact: 02-design-ui.md
next_action: "/architect lee 01+02 → produce 03-arch-* + 04-tickets.yaml"
```

## Live verification

Antes de declarar done, opcional pero recomendado:
- Invocar `chrome-devtools-verify` para validar mockup en dev-app.nicolify.com (si la pantalla ya existe parcial)
- O bash + python3 -m http.server para Chris vea HTML local

## Anti-patterns

- ❌ Rebuild from scratch en cada iteración
- ❌ Hardcoded hex colors / spacing / fontsize
- ❌ Inventar componentes que no existen sin flag explícito en design.md
- ❌ Lorem ipsum / placeholder data genérico
- ❌ Voseo en UI strings
- ❌ Hide scope conflicts del user (always escalate visible)
- ❌ Skip mandatory skill invocation
- ❌ Proponer features fuera scope sin escalate
- ❌ Diseñar arq técnica (es /architect) o data flow técnico (lo declarás conceptual, /architect-fe lo concreta en hooks)
- ❌ Producir 02-design-ui.md sin haber iterado mínimo 1 ronda con Chris

## Output format

Cada iteración: HTML mockup + 1 frase resumen + pregunta cierre. NUNCA dumps largos.
