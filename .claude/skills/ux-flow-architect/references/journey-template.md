# Journey Mapping Template

Use this format for Phase 2 journey documentation. Each journey should be a standalone section that can be embedded in the FLOW-SPEC.

---

## Journey Documentation Format

```markdown
### Journey: [Name]

**Persona:** [User archetype — e.g., "Creadora de contenido, 30-45 años, primera vez en la plataforma"]
**Trigger:** [What starts this journey — e.g., "Acaba de registrarse y completar onboarding"]
**Goal:** [What the user wants to achieve — e.g., "Tener su marca configurada y lista para vender"]
**Frequency:** [How often this journey occurs — Daily / Weekly / Monthly / One-time]
**Priority:** [User-assigned — Critical / Important / Nice-to-have]

#### Step-by-Step Walkthrough

| # | User Intent | Action | Route | Nav Element | Status | Notes |
|---|-------------|--------|-------|-------------|--------|-------|
| 1 | "Quiero configurar mi negocio" | Llega al dashboard | /[tenantId]/ | Auto-redirect | ✅ OK | |
| 2 | "Qué debo hacer primero?" | Ve Brand Studio en sidebar | /brand-studio/esencia | Sidebar | ✅ OK | |
| 3 | "Ya terminé mi marca, ¿ahora qué?" | Busca siguiente paso | ??? | ??? | ❌ Missing | No hay CTA |
| ... | | | | | | |

#### Status Legend

| Status | Meaning |
|--------|---------|
| ✅ OK | User can complete this step with clear, intuitive navigation |
| ⚠️ Friction | Step is technically possible but requires extra clicks, guessing, or help |
| ❌ Missing | No navigation element exists to guide the user to this step |
| 🔄 Redirect | Page exists but auto-redirects (may confuse user) |

#### Friction Points

List every ⚠️ step with details:

| Step | Friction Type | Description | Severity |
|------|--------------|-------------|----------|
| 3 | Cognitive | User has to figure out what to do next on their own | High |
| 5 | Navigation | Button exists but label is unclear ("Ver más" — ver más de qué?) | Medium |
| 7 | Technical | Page loads slowly because of N+1 queries | Low |

**Friction Types:**
- **Cognitive:** User has to think about what to do / where to go
- **Navigation:** Path exists but is hidden, unclear, or requires too many clicks
- **Technical:** Performance, loading, or error issues that interrupt the flow
- **Labeling:** Button/link text doesn't match user's mental model
- **Context loss:** User loses track of where they are or what they were doing

#### Dead Ends

Pages where the user gets stuck with no clear next action:

| Step | Page | What's Missing |
|------|------|---------------|
| 3 | /brand-studio/esencia | No "siguiente paso" CTA after completing brand setup |
| 8 | /offer-studio/offer/[id]/knowledge | Page has content but no link to create campaign from this offer |

#### Missing Connections

Logical bridges between pages that should exist but don't:

| From (Step) | To (Step) | Type | Description |
|-------------|-----------|------|-------------|
| 3 → 4 | Brand → Offer | CTA | "Tu marca está lista. Crea tu primera oferta →" |
| 6 → 7 | Offer → Growth | CTA | "Oferta publicada. Lanza una campaña para atraer leads →" |
| 9 → 10 | Growth → Sales | Deep link | "12 leads nuevos → Ver en inbox" |

#### Journey Diagram

ASCII representation of the complete journey with status:

```
[Sign Up] ✅
    ↓
[Onboarding] ✅
    ↓
[Brand Studio: Esencia] ✅
    ↓
  ??? ❌  ← dead end (no next step)
    ↓ (should be)
[Offer Studio: Crear Oferta] ⚠️
    ↓
[Growth Studio: Campaña] ⚠️
    ↓
[Sales: Inbox] ✅
```
```

---

## Canonical Journeys for Nicolify

When running a full audit, map these 4 journeys at minimum. The user may add or skip journeys.

### 1. Onboarding: Registro → Primer Valor

- **Start:** Sign-up / Onboarding
- **End:** First lead captured or first sale
- **Key question:** "Can a new user go from zero to their first lead without getting lost?"
- **Critical path:** Sign-up → Brand Setup → Create Offer → Connect Channel → Launch Campaign → See First Lead

### 2. Daily Use: Returning User → Revisar y Actuar

- **Start:** Open app (returning user)
- **End:** Complete one meaningful action (respond to lead, check metrics, adjust campaign)
- **Key question:** "Does the dashboard show the most relevant info, or does the user have to dig?"
- **Critical path:** Dashboard → Growth Summary → Sales Inbox → Respond to Lead → Back to Dashboard

### 3. Offer Lifecycle: Crear → Publicar → Medir

- **Start:** Idea for a new offer
- **End:** See conversion data for that offer
- **Key question:** "Can the user go from creating an offer to measuring its success in one coherent flow?"
- **Critical path:** Offer Studio → Create Offer → Configure Landing → Set Campaign → Growth Studio → See Metrics

### 4. Sales Pipeline: Lead → Cierre

- **Start:** New lead appears
- **End:** Deal closed (payment link sent, event scheduled)
- **Key question:** "Can the user manage the full sales cycle without leaving Closer Studio?"
- **Critical path:** Growth notification → Sales Inbox → Conversation → Pipeline → Close → Post-sale

---

## Interactive Walkthrough Script

During Phase 2, walk each journey step-by-step with the user. Use this script:

1. **Announce the journey:** "Vamos a recorrer el flujo de [journey name]. El usuario empieza en [start point]."

2. **At each step, ask:**
   - "Si estás en [current page], ¿cómo llegas a [next expected page]?"
   - If unclear: Read the actual page component to check for links/CTAs
   - "¿Este paso es intuitivo o requiere que el usuario 'ya sepa' dónde ir?"

3. **At dead ends, confirm:**
   - "No encontré ningún enlace de [current] a [expected next]. ¿Es correcto que no existe?"
   - "¿Esto es intencional o es un gap?"

4. **At the end, summarize:**
   - "El journey de [name] tiene N pasos, M friction points, K dead ends."
   - "Los gaps más críticos son: [list]"
   - "¿Quieres profundizar en alguno, o pasamos al siguiente journey?"

---

## Questions to ask the user per journey

After walking through each journey:

1. "¿Qué tan frecuente es este flujo para tus usuarios?" (define priority)
2. "¿Hay algún paso que yo no haya considerado?"
3. "¿Algún paso debería ser automático en vez de manual?"
4. "Si pudieras eliminar un solo punto de fricción de este flujo, ¿cuál sería?"
