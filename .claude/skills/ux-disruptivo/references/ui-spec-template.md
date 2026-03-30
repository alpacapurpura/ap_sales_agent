# UI-SPEC Template (Enhanced)

Use this template for Phase 7 output. Fill every section. Mark sections N/A only if truly not applicable.

---

```markdown
# UI Spec: [Feature Name]

## Design Intent
- **Concept:** [Creative concept name/metaphor from Phase 5]
- **Problem solved:** [From Phase 2 problem_statement]
- **Target emotion:** [What the user should feel — clarity, control, confidence, speed...]
- **Design approach:** [1 sentence: why this layout/pattern was chosen]

## Persona
- **Primary user:** [Archetype from Phase 1]
- **Context:** [When they arrive, what they know, what they need]
- **Technical level:** [Low / Medium / High]
- **Secondary user:** [If any]

## Design Principles
[3 principles extracted from Phase 4 research that guide this design]

1. **[Principle name]** — [1-sentence explanation]
2. **[Principle name]** — [1-sentence explanation]
3. **[Principle name]** — [1-sentence explanation]

## Layout Mockup

### Desktop (≥1024px)
```
[ASCII mockup — see ascii-mockup-guide.md]
```

### Mobile (<768px)
```
[ASCII mockup — mobile adaptation]
```

## Component Tree

```
[PageName] (Server Component — src/app/{tenant}/{route}/page.tsx)
├── [ComponentA] (Server — src/features/{domain}/ui/component-a.tsx)
│   ├── ShadcnComponent (Shadcn)
│   └── ShadcnComponent (Shadcn)
├── [ComponentB] (Client — needs useState/useEffect)
│   ├── ShadcnComponent (Shadcn)
│   └── [SubComponent] (Client)
└── [ComponentC] (Client — form with state)
    ├── Form (Shadcn + React Hook Form + Zod)
    └── Button (Shadcn)
```

## Data Flow

### Server-Side (Page)
```
page.tsx (RSC)
  → [How data is fetched and passed down]
```

### Client-Side (Interactive Components)
```
[ComponentB] ("use client")
  → [What hooks, what state, what mutations]

[ComponentC] ("use client")
  → [Form handling, validation, submission]
```

## API Integration

| Component | Hook | API Call | Trigger |
|-----------|------|----------|---------|
| ComponentB | useXxx() | GET /api/v1/... | Mount |
| ComponentC | useCreateXxx() | POST /api/v1/... | Form submit |

## Interaction Patterns

| Trigger | Animation | Duration | Component | Notes |
|---------|-----------|----------|-----------|-------|
| Panel open | fade-in + slide-up | 200ms | DetailPanel | animate-fade-in class |
| Delete confirm | alert-dialog | — | Row action | Requires explicit confirm |
| Form submit | button loading | until response | Submit button | Disable + spinner |
| Success | toast | 3s auto-dismiss | Sonner | Bottom-right |

## Shadcn Components Used

| Component | Import | Usage |
|-----------|--------|-------|
| Card | `@/components/ui/card` | [specific usage] |
| Button | `@/components/ui/button` | [specific usage] |
| ... | ... | ... |

## FSD File Structure

```
frontend/src/features/{domain}/
├── components/
│   ├── component-a.tsx        (Server Component)
│   ├── component-b.tsx        (Client Component)
│   └── component-c.tsx        (Client Component)
├── types/
│   └── index.ts               (TypeScript interfaces from CONTRACT.md)
├── api/
│   └── {entity}-api.ts        (API functions)
├── hooks/
│   ├── use-xxx.ts             (useQuery hook)
│   └── use-create-xxx.ts      (useMutation hook)
└── index.ts                   (Public API exports)
```

## Responsive Behavior

| Breakpoint | Layout Changes |
|------------|----------------|
| Desktop (≥1024px) | [Default layout as in mockup] |
| Tablet (768-1023px) | [Specific adaptations] |
| Mobile (<768px) | [Stack columns, hide sidebar, sheet instead of dialog, etc.] |

## Loading, Error, & Empty States

| State | Component | Behavior |
|-------|-----------|----------|
| Loading | [Component] | [Skeleton pattern — how many, what shape] |
| Empty | [Component] | [Message + CTA to guide user] |
| Error | [Component] | [Alert with retry button] |
| Submitting | [Form] | [Button disabled + spinner, form fields read-only] |

## Visual Design

### Spacing Scale
| Element | Spacing |
|---------|---------|
| Section gap | [e.g., gap-6 / 24px] |
| Card padding | [e.g., p-4 / 16px] |
| Between form fields | [e.g., gap-4 / 16px] |

### Typography
| Element | Class | Weight |
|---------|-------|--------|
| Page title | text-2xl | font-bold |
| Section title | text-lg | font-semibold |
| Body text | text-sm | font-normal |
| Label | text-sm | font-medium |
| Helper text | text-xs | text-muted-foreground |

### Color Distribution (60/30/10)
| Role | Token | Usage |
|------|-------|-------|
| 60% Base | `background` / `card` | Page and card backgrounds |
| 30% Supporting | `muted` / `secondary` | Section dividers, badges, subtle areas |
| 10% Accent | `primary` / `destructive` | CTAs, critical actions, key metrics |

### Copywriting Contract
| Element | Text | Tone |
|---------|------|------|
| Page title | "[Title]" | [Professional / Friendly / Direct] |
| Empty state heading | "[Heading]" | [Encouraging] |
| Empty state CTA | "[Button text]" | [Action-oriented] |
| Error message | "[Message]" | [Helpful, not blaming] |
```

---

## Checklist (before writing)

- [ ] All component names are valid (checked against codebase)
- [ ] All Shadcn components exist in `frontend/src/components/ui/`
- [ ] FSD paths follow project conventions
- [ ] Server/Client boundary is correct (no unnecessary "use client")
- [ ] All API endpoints match CONTRACT.md (if available)
- [ ] Loading, error, and empty states specified for every data component
- [ ] Responsive behavior defined for all breakpoints
- [ ] Design Intent reflects the creative process (Phases 1-4)
