# SaaS Navigation Patterns

Reference catalog of navigation patterns for Phase 4 proposals. When proposing flow improvements, reference these patterns by name and explain the UX principle behind each choice.

---

## 1. Hub-and-Spoke Dashboard

**What:** Central dashboard home that links to all studios/sections via cards or widgets.
**When to use:** When returning users need a daily summary before diving into any studio.
**UX Principle:** Overview first, details on demand (Shneiderman's mantra).

**Example apps:** HubSpot (dashboard tiles), Shopify (admin home), Notion (home page).

```
┌─────────────────────────────────────────────────────────┐
│  Buenos días, [Name]               [Notifications] [⚙]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 📊 Growth     │  │ 💬 Sales      │  │ 🎨 Brand      │  │
│  │ 47 leads hoy │  │ 3 conv. open │  │ 85% completo │  │
│  │ "Ver métricas"│  │ "Ver inbox"  │  │ "Continuar"  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  📋 Próximos pasos                               │    │
│  │  ☐ Configura tu primera oferta                   │    │
│  │  ☐ Conecta tu cuenta de Instagram                │    │
│  │  ☐ Revisa leads de esta semana                   │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**Trade-offs:**
- ✅ Returning users see what matters immediately
- ✅ Discovery: all features visible at a glance
- ⚠️ New users may feel overwhelmed
- ⚠️ Requires backend aggregation endpoints

---

## 2. Contextual Next-Step CTAs

**What:** After completing an action on page A, a CTA suggests the logical next step on page B.
**When to use:** When studios have a natural sequential flow (Brand → Offer → Growth → Sales).
**UX Principle:** Progressive disclosure + Nudge theory.

**Example apps:** Webflow (after publishing, suggests SEO), Mailchimp (after creating campaign, suggests audience).

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ✅ Brand configurado exitosamente                       │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Siguiente paso sugerido                         │    │
│  │  Tu marca está lista. Ahora crea tu primera     │    │
│  │  oferta para empezar a vender.                   │    │
│  │                            "Crear Oferta →"      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation:** Add a `<NextStepBanner>` component that reads user progress and suggests the next incomplete step. Requires a progress tracking system.

**Trade-offs:**
- ✅ Zero cognitive load — user doesn't have to think about what's next
- ✅ Guides new users through the full setup flow
- ⚠️ Can feel prescriptive to power users
- ⚠️ Needs progress tracking data

---

## 3. Breadcrumb Trails

**What:** Hierarchical breadcrumbs showing the path to the current page.
**When to use:** For deep routes (3+ levels) or when users need to navigate up the hierarchy.
**UX Principle:** Location awareness (wayfinding).

**Example apps:** Linear (project → issue → sub-issue), AWS Console (service → resource → detail).

```
Brand Studio > Público > María, Emprendedora Digital
```

**Nicolify specifics:** Useful for:
- `/brand-studio/publico/persona/[personaId]` → Brand Studio > Público > [Persona Name]
- `/offer-studio/offer/[id]/assets` → Offer Studio > [Offer Name] > Assets
- `/growth-studio/atraccion-captura/[channelSlug]` → Growth Studio > Atracción > [Channel Name]

**Trade-offs:**
- ✅ Always shows where you are
- ✅ Quick jump to any parent level
- ⚠️ Takes vertical space on mobile
- ⚠️ Can get long for very deep routes

---

## 4. Onboarding Checklist Overlay

**What:** Persistent (dismissible) progress checklist that guides new users through initial setup.
**When to use:** First-time users who need to complete a multi-step setup across different studios.
**UX Principle:** Goal gradient effect — users accelerate as they approach completion.

**Example apps:** Notion (getting started guide), Stripe (activation checklist), Linear (workspace setup).

```
┌──────────────────────────────┐
│  Tu progreso: 2/5 pasos      │
│  ████████░░░░░░░░░░░ 40%     │
│                              │
│  ✅ Configura tu marca        │
│  ✅ Agrega tu logo            │
│  ☐ Crea tu primera oferta    │  ← "Ir →"
│  ☐ Conecta Instagram         │
│  ☐ Configura tu agente AI    │
│                              │
│  [Ocultar por ahora]        │
└──────────────────────────────┘
```

**Implementation:** Floating card (bottom-right) or collapsible sidebar section. Each step links to the relevant studio/page. Dismiss after all complete or after user clicks "ocultar".

**Trade-offs:**
- ✅ Dramatically improves completion rates
- ✅ Cross-studio — bridges the journey naturally
- ⚠️ Needs progress tracking backend
- ⚠️ Must be easily dismissible or it annoys returning users

---

## 5. Command Palette (Cmd+K)

**What:** Quick-access search/action palette triggered by keyboard shortcut.
**When to use:** For power users who want to jump directly to any feature without sidebar navigation.
**UX Principle:** Direct access for expert users (efficiency of use).

**Example apps:** Linear (Cmd+K), Notion (Cmd+K), Vercel (Cmd+K), Raycast.

```
┌─────────────────────────────────────────┐
│  🔍 Buscar o ejecutar...                 │
├─────────────────────────────────────────┤
│  Recientes                              │
│  📊 Growth Studio > Atracción            │
│  💬 Sales > Inbox                        │
│                                         │
│  Navegación                             │
│  🎨 Brand Studio > Esencia              │
│  📦 Offer Studio                         │
│  ⚙️ Configuración > Conexiones          │
│                                         │
│  Acciones                               │
│  + Crear nueva oferta                   │
│  + Conectar cuenta                      │
│  + Iniciar campaña                      │
└─────────────────────────────────────────┘
```

**Trade-offs:**
- ✅ Zero friction for power users
- ✅ Surfaces ALL features, including orphaned routes
- ⚠️ Invisible to new users (keyboard shortcut discovery problem)
- ⚠️ Moderate implementation effort (search index, recent tracking)

---

## 6. Contextual Cross-Links (In-Page)

**What:** Links within page content that connect to related features in other studios.
**When to use:** When two features are logically related but in different studios.
**UX Principle:** Contextual navigation (show links where they're relevant, not just in a global nav).

**Example:** In Growth Studio's campaign detail, show a link "Edit this offer" that goes to Offer Studio.

```
┌─────────────────────────────────────────┐
│  Campaña: Lanzamiento Coaching 1:1      │
│                                         │
│  Oferta asociada: Coaching 1:1          │
│  [Ver en Offer Studio →]               │
│                                         │
│  Canal: Instagram Orgánico              │
│  [Ver conexión →]                       │
└─────────────────────────────────────────┘
```

**Trade-offs:**
- ✅ Connects features where it makes sense
- ✅ No sidebar restructure needed
- ⚠️ Can clutter pages with too many links
- ⚠️ Bidirectional links need maintenance

---

## 7. Tab Groups Within Studio

**What:** Organize related features as tabs within a studio, instead of separate sidebar entries.
**When to use:** For features that share a context but are different "views" of the same domain.
**UX Principle:** Grouping related information reduces navigation cost.

**Example:** Brand Studio currently has some features as sidebar entries and others orphaned. Could group them as tabs:

```
Brand Studio
┌────────────────────────────────────────────────────────┐
│  [Esencia] [Estrategia] [Público] [Identidad] [Assets]│
├────────────────────────────────────────────────────────┤
│                                                        │
│  [Tab content here]                                    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Trade-offs:**
- ✅ All features discoverable within the studio
- ✅ No sidebar pollution (sidebar stays clean)
- ⚠️ Too many tabs can overwhelm (max 5-7)
- ⚠️ Deep features within tabs need breadcrumbs

---

## 8. "Smart Default" Landing

**What:** Dashboard root adapts to user state — new users see onboarding, returning users see activity summary.
**When to use:** When the "right" landing page depends on where the user is in their lifecycle.
**UX Principle:** Personalized relevance.

**Example apps:** Shopify (new store → setup wizard; existing → orders dashboard), GitHub (new → explore; existing → feed).

```
IF user.has_completed_brand:
  IF user.has_active_conversations:
    → redirect to Sales/Inbox
  ELIF user.has_active_campaigns:
    → redirect to Growth Studio
  ELSE:
    → redirect to Dashboard Home
ELSE:
  → redirect to Brand Studio/Esencia (current behavior, correct for new users)
```

**Trade-offs:**
- ✅ Every user lands on the most relevant page
- ⚠️ Users may be confused if landing changes unexpectedly
- ⚠️ Needs user lifecycle state tracking
- ⚠️ Consider: add a "set default view" preference

---

## Combining Patterns

Patterns are not mutually exclusive. Recommended combinations:

| User Stage | Patterns |
|-----------|----------|
| First visit | Onboarding Checklist (#4) + Smart Landing (#8 → brand setup) |
| Setup in progress | Contextual CTAs (#2) + Breadcrumbs (#3) |
| Active daily user | Hub Dashboard (#1) + Command Palette (#5) + Cross-Links (#6) |
| Power user | Command Palette (#5) + Tab Groups (#7) + Breadcrumbs (#3) |

When proposing in Phase 4, recommend a combination that matches the user's target persona, not a single pattern.
