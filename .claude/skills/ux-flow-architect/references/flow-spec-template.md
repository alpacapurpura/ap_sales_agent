# FLOW-SPEC Template

Use this template for Phase 6 output. Fill every section. Mark sections N/A only if truly not applicable (e.g., studio-scoped audit may skip some journeys).

---

```markdown
# Flow Spec: [Scope — e.g., "Full Application" or "Brand Studio"]

## Audit Summary

| Metric | Count |
|--------|-------|
| Total routes | N |
| Sidebar-visible routes | N |
| Studio-internal routes (tabs/sub-nav) | N |
| Deep-linked routes (reachable via in-page links) | N |
| Orphaned routes (no navigation path) | N |
| Redirect-only routes | N |
| Admin-only routes | N |

## Current Navigation Map

### Sidebar Structure

```
├── [Group 1]
│   ├── [Entry] → /route
│   ├── [Entry] → /route
│   └── [Entry] → /route
├── [Group 2]
│   └── [Entry] → /route
└── [Group N]
    ├── [Entry] → /route
    └── [Entry] → /route
```

### Studio-Internal Navigation

| Studio | Nav Type | Items |
|--------|----------|-------|
| Brand Studio | Tabs (sections config) | Esencia, Estrategia, Público, Identidad Creativa |
| Offer Studio | Offer shell tabs | Editor, Assets, Campaigns, Knowledge |
| Growth Studio | Stage layout | Atracción, Nutrición, Ventas, Adopción, Expansión |
| Closer Studio | Layout tabs | Inbox, Pipeline, Frozen |

### Deep Links (in-page navigation)

| Source Page | Target Page | Trigger Element | Type |
|-------------|-------------|-----------------|------|
| [source route] | [target route] | [button/link/card text] | CTA / Link / Redirect |

### Orphaned Routes

| Route | Feature Module | Purpose | Severity |
|-------|---------------|---------|----------|
| [route] | [features/domain] | [what it does] | Critical / Medium / Low |

## Journey Maps

### Journey 1: [Name — e.g., "Nuevo Usuario: Setup → Primer Valor"]

**Persona:** [Archetype — e.g., "Creador de contenido, primera vez en la plataforma"]
**Trigger:** [What starts this journey — e.g., "Completa sign-up y onboarding"]
**Frequency:** [Daily / Weekly / One-time]
**Priority:** [Critical / Important / Nice-to-have]

| Step | User Action | Expected Route | Nav Element | Status |
|------|-------------|----------------|-------------|--------|
| 1 | [action] | [/route] | [sidebar/tab/CTA/link] | ✅ OK / ⚠️ Friction / ❌ Missing |
| 2 | [action] | [/route] | [element] | [status] |
| N | [action] | [/route] | [element] | [status] |

**Friction Points:**
- [Step N]: [description of friction — extra clicks, unclear labeling, etc.]

**Dead Ends:**
- [Step N]: [page where user gets stuck with no clear next action]

**Missing Connections:**
- [Step N → Step N+1]: [no CTA/link exists to bridge these steps]

---

[Repeat for each journey]

## Gap Analysis

### Priority Matrix

| # | Finding | Category | Impact | Effort | Priority |
|---|---------|----------|--------|--------|----------|
| 1 | [finding] | Orphaned / Dead-end / Missing-link / Architecture | High/Med/Low | High/Med/Low | P1/P2/P3 |

### Orphaned Features (Detail)

| # | Route | Feature | Who needs it | Proposed placement | Priority |
|---|-------|---------|--------------|-------------------|----------|
| 1 | [route] | [description] | [persona] | [sidebar group / tab / CTA from X] | P1/P2/P3 |

### Missing Connections (Detail)

| # | From | To | Connection Type | Rationale | Priority |
|---|------|-----|----------------|-----------|----------|
| 1 | [source page] | [target page] | CTA / Link / Redirect / Breadcrumb | [why this connection matters] | P1/P2/P3 |

### Architecture Issues

| # | Issue | Current Behavior | Proposed Behavior | Priority |
|---|-------|-----------------|-------------------|----------|
| 1 | [structural issue] | [what happens now] | [what should happen] | P1/P2/P3 |

## Proposed Changes

### Sidebar Restructure

```
BEFORE:                              AFTER:
├── [Group]                          ├── [Group]
│   ├── [Entry]                      │   ├── [Entry]
│   └── [Entry]                      │   ├── [Entry] (NEW)
...                                  │   └── [Entry] (MOVED)
                                     ...
```

### Navigation Changes

| # | Change | Type | Files Affected | Effort | Priority |
|---|--------|------|---------------|--------|----------|
| 1 | [description] | Sidebar / CTA / Redirect / Tab / Breadcrumb | [file paths] | Low/Med/High | P1/P2/P3 |

### New Components Needed

| Component | Purpose | Location (FSD) | Effort |
|-----------|---------|---------------|--------|
| [name] | [what it does] | frontend/src/features/... or components/shared/ | Low/Med/High |

### New Routes Needed

| Route | Page Purpose | Studio | Requires Backend? |
|-------|-------------|--------|-------------------|
| /[tenantId]/[route] | [description] | [studio name] | Yes / No |

## File Changes Required

| File | Change Type | Description |
|------|------------|-------------|
| `frontend/src/components/shared/layout/app-sidebar.tsx` | Modify | [what changes] |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/page.tsx` | Modify | [what changes] |
| [path] | Create / Modify | [description] |

## Prototype Reference

- **Preview URL:** `http://localhost:8888`
- **Preview directory:** `/tmp/nicolify-flow-preview/`
- **Pages:**

| File | Represents Route | Journey(s) |
|------|-----------------|------------|
| index.html | / (root redirect) | All |
| [file] | /[route] | [journey names] |

## Implementation Order

### Phase 1: Quick Wins (sidebar entries + redirects)
Effort: Low. No new pages. Just wiring existing features to navigation.

1. [change]
2. [change]

### Phase 2: New Pages (dashboard home, missing screens)
Effort: Medium. Requires design (invoke `ux-disruptivo` for each).

1. [change — link to UI-SPEC if exists]
2. [change]

### Phase 3: Cross-Studio Connections (CTAs, contextual links)
Effort: Medium-High. Requires understanding cross-domain context.

1. [change]
2. [change]

### Phase 4: Onboarding & Discovery (getting started, tooltips)
Effort: Variable. UX polish layer.

1. [change]
2. [change]

## Delta UI-SPECs Generated

| File | Scope | Status |
|------|-------|--------|
| `docs/ui-specs/UI-SPEC-sidebar-restructure.md` | Sidebar navigation changes | Ready |
| `docs/ui-specs/UI-SPEC-dashboard-home.md` | New dashboard home page | Requires `ux-disruptivo` design |
| [path] | [scope] | [status] |
```

---

## Section-by-section guidance

### Audit Summary
Pure numbers. Keep it factual. The skill auto-generates this from Phase 1 codebase scan.

### Journey Maps
Each journey must have:
- Clear start and end points
- Every intermediate step with its route
- Status annotation per step (OK / Friction / Missing)
- At least one friction point or dead end identified (if none, the journey is healthy — mark it so)

### Gap Analysis
Priority criteria:
- **P1 (Critical):** User cannot complete a key journey. Feature is actively hiding value.
- **P2 (Important):** User can work around it but experience is degraded. Extra clicks, confusion.
- **P3 (Nice-to-have):** Improvement that would polish the experience but not blocking anyone.

### Proposed Changes
Each change must reference:
- Which gap(s) it addresses (by number from Gap Analysis)
- Exact files that need modification
- Effort estimate

### Implementation Order
Group by dependency, not by priority. Phase 1 must complete before Phase 2 can start (sidebar entries need to exist before CTAs can link to them).
