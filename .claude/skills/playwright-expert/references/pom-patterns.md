# Page Object Models — Patterns + Locator Priority

> **Read when:** writing or refactoring a POM, choosing a locator, debugging "element not found," seeing a teammate write CSS-class selectors.

POMs are the abstraction that lets test specs remain stable as the FE evolves. A well-designed POM hides every brittle detail (CSS classes, DOM structure, exact text) behind a method name that reflects user intent. A badly-designed POM leaks those details and breaks every time Tailwind generates a new class hash.

---

## 1. Locator priority — non-negotiable order

Use the highest-priority locator available. If you find yourself reaching for #5 or below, stop and ask "is the FE missing a semantic primitive?" — usually the answer is yes, and adding `aria-label` to the FE component is the right fix, not introducing a CSS locator in the test.

| Priority | API | When to use |
|---|---|---|
| 1 | `page.getByRole(role, { name })` | Default for all interactive elements: `'button'`, `'link'`, `'textbox'`, `'heading'`, `'dialog'`, `'menu'`, `'tab'`, `'cell'`, `'row'` |
| 2 | `page.getByLabel(text)` | Form inputs that have an associated `<label>`. Use when the visible text is the label, not the placeholder |
| 3 | `page.getByPlaceholder(text)` | Form inputs without a visible label (use sparingly; prefer adding a label) |
| 4 | `page.getByText(text \| regex)` | Static informational text — paragraphs, captions, badges. Avoid for interactive elements |
| 5 | `page.getByTestId('feature-element')` | Last resort for things without a meaningful role; the FE must add `data-testid="..."` |
| ❌ | `page.locator('.css-class')` / `page.locator('//xpath')` | NEVER. Tailwind class hashes change; XPath is brittle |

**Why role-first:** the role is what an assistive technology user perceives. If your test passes by selecting "the button labeled 'Save'", it implicitly tests that the page is accessible. CSS-based locators give you a passing test on an inaccessible page — a false positive.

### Examples by locator type

```typescript
// 1. Role
page.getByRole('button', { name: 'Crear oferta' })
page.getByRole('heading', { level: 1, name: /brand studio/i })
page.getByRole('dialog')                       // entire modal
page.getByRole('row').filter({ hasText: 'Juan Pérez' })   // a table row
page.getByRole('cell', { name: 'pendiente' }) // a table cell
page.getByRole('tab', { name: 'Identidad' })

// 2. Label (form fields)
page.getByLabel('Nombre del proyecto')
page.getByLabel(/email/i)                      // case-insensitive

// 3. Placeholder (only when no label)
page.getByPlaceholder('hola@ejemplo.com')

// 4. Text (informational)
page.getByText('Sin resultados')
page.getByText(/^total:/i)                     // anchor with regex

// 5. Test ID (escape hatch)
page.getByTestId('copilot-drawer')             // matches data-testid="copilot-drawer"
```

---

## 2. The three POM responsibilities

A POM does three things, in this order:

1. **Owns the locators** for one page or one closely-related set of pages.
2. **Exposes user-intent methods** that compose actions on those locators.
3. **Provides assertion helpers** for the page's "loaded" state.

It does NOT:
- Make API calls (that's mock setup, lives in fixtures)
- Set up auth (that's `auth.fixture.ts`)
- Hold its own state across tests (each test gets a fresh POM instance)
- Handle navigation between unrelated pages (each page = its own POM, even if the user moves between them)

---

## 3. Anatomy of a high-quality POM

Pattern from `frontend/e2e/pages/navigation.page.ts` (the canonical example):

```typescript
import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class BrandStudioPage {
  readonly page: Page;

  // === Locators (declared once, in the constructor) ===
  readonly heading: Locator;
  readonly identityTab: Locator;
  readonly storyTab: Locator;
  readonly visualsTab: Locator;
  readonly saveButton: Locator;
  readonly toastSuccess: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: /brand studio/i });
    this.identityTab = page.getByRole('tab', { name: /identidad/i });
    this.storyTab = page.getByRole('tab', { name: /historia/i });
    this.visualsTab = page.getByRole('tab', { name: /visuales/i });
    this.saveButton = page.getByRole('button', { name: /guarda/i });
    this.toastSuccess = page.getByRole('status').filter({ hasText: /guardado/i });
  }

  // === Navigation ===
  async goto(tenantId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/brand-studio`);
  }

  // === Actions (one per user intent, imperative naming) ===
  async openIdentitySection(): Promise<void> {
    await this.identityTab.click();
  }

  async fillBrandName(name: string): Promise<void> {
    await this.page.getByLabel(/nombre de la marca/i).fill(name);
  }

  async clickSave(): Promise<void> {
    await this.saveButton.click();
  }

  // === Assertions (declarative; web-first) ===
  async expectLoaded(): Promise<void> {
    await expect(this.heading).toBeVisible({ timeout: 10_000 });
    await expect(this.identityTab).toBeVisible();
  }

  async expectSaved(): Promise<void> {
    await expect(this.toastSuccess).toBeVisible({ timeout: 5_000 });
  }
}
```

### What makes this POM good

- **Constructor is the locator catalogue.** All locators discoverable in one place; no surprises hiding deep in methods.
- **Methods are user verbs.** `openIdentitySection()`, `clickSave()`, `fillBrandName()`. A reader infers behavior without looking at the spec.
- **Assertions are dedicated methods.** The spec calls `await page.expectLoaded()` instead of inlining `await expect(page.heading).toBeVisible()`. This makes specs read like English.
- **Locators use case-insensitive regex** (`/identidad/i`) so they survive pluralization or capitalization tweaks in the FE copy.
- **No dependencies on internal state.** `expectLoaded` only checks DOM; doesn't peek at network or storage.

---

## 4. Multi-page flows — composition, not inheritance

When a flow spans two pages (e.g., "create campaign → land on detail page"), use TWO POMs in the spec, not one mega-POM:

```typescript
test('campaign create flow', async ({ page, tenantId }) => {
  const campaigns = new CampaignsListPage(page);
  await campaigns.goto(tenantId);
  await campaigns.openCreateDialog();
  await campaigns.fillName('Test Q3');
  await campaigns.submit();

  const detail = new CampaignDetailPage(page);  // same `page`, different POM
  await detail.expectLoaded();
  await expect(detail.statsCard).toBeVisible();
});
```

This is cleaner than a `CampaignsFlowPage` mega-class with 30 methods.

---

## 5. Common locator recipes (Nicolify-specific)

### Tables (Shadcn `<Table>` + Tanstack)

```typescript
// Whole table
page.getByRole('table')

// Specific row by content
page.getByRole('row').filter({ hasText: 'Juan Pérez' })

// Cell within a row by column header
page.getByRole('row', { name: /juan pérez/i })
    .getByRole('cell')
    .nth(2)                                    // 3rd column

// Header cell
page.getByRole('columnheader', { name: /email/i })

// All rows except header
page.getByRole('row').filter({ hasNot: page.getByRole('columnheader') })
```

### Dialogs / Modals (Radix UI via Shadcn)

```typescript
// Whole dialog
page.getByRole('dialog')

// Field inside dialog (scoped to avoid collisions)
page.getByRole('dialog').getByLabel(/nombre/i)

// Close button (Radix exposes aria-label)
page.getByRole('dialog').getByRole('button', { name: /cerrar|close/i })
```

### Tabs (Shadcn `<Tabs>`)

```typescript
page.getByRole('tab', { name: /identidad/i }).click()
await expect(page.getByRole('tabpanel', { name: /identidad/i })).toBeVisible()
```

### Toasts (Sonner via Shadcn)

```typescript
// Toast region has role="status" or role="alert"
page.getByRole('status').filter({ hasText: /guardado/i })
page.getByRole('alert').filter({ hasText: /error/i })
```

### Forms (RHF + Shadcn `<Form>`)

```typescript
page.getByLabel(/email/i).fill('hola@ejemplo.com')
page.getByLabel(/contraseña/i).fill('secret')
page.getByRole('button', { name: /enviar|guarda/i }).click()
```

### Sidebar / Navigation

```typescript
// Sidebar items are typically <a> with text
page.getByRole('link', { name: /brand studio/i })
page.getByRole('navigation').getByRole('link', { name: /ofertas/i })
```

---

## 6. Filters and chaining — the power tools

When `getByRole` returns multiple matches, narrow with `.filter()`:

```typescript
// "The Save button INSIDE the dialog, not the page-level one"
page.getByRole('dialog').getByRole('button', { name: /guarda/i })

// "The row that contains 'pendiente' AND has Juan in the name column"
page.getByRole('row')
    .filter({ hasText: 'Juan' })
    .filter({ hasText: 'pendiente' })

// "The first list item containing 'producto'"
page.getByRole('listitem').filter({ hasText: 'producto' }).first()

// "The button to add to cart, in the Product 2 row"
page.getByRole('listitem')
    .filter({ hasText: 'Product 2' })
    .getByRole('button', { name: 'Add to cart' })
    .click()
```

Chaining is an explicit, readable narrowing — much better than `.nth(2)` which silently breaks when the order changes.

---

## 7. Ambiguity — `.first()` vs `.nth()` vs `.filter()`

When a locator matches > 1 element:

- **`.filter({ hasText: '...' })`** — the right answer most of the time. Says "I want the one that mentions X."
- **`.first()`** — acceptable when you genuinely don't care which (e.g., "any of these checkboxes"). Document with a comment.
- **`.nth(N)`** — last resort. Brittle. Use only when DOM order is genuinely meaningful (e.g., "the first row in a sorted-by-date table").
- **`.last()`** — almost always wrong; use `.filter()` to find the specific element.

Strict mode (default) will throw if a locator matches > 1 and you didn't narrow. Embrace this — it forces you to be explicit.

---

## 8. Auto-retrying assertions vs manual checks

Always use **web-first assertions** that auto-retry until the timeout:

```typescript
// ✅ retries until visible OR timeout
await expect(page.getByText('Guardado')).toBeVisible()

// ❌ snapshots once; flake guarantee
expect(await page.getByText('Guardado').isVisible()).toBe(true)

// ❌ literally hardcodes a wait — flaky in slow CI, slow when fast
await page.waitForTimeout(1000)
```

Web-first matchers we use most:
- `await expect(locator).toBeVisible()` / `.toBeHidden()`
- `await expect(locator).toHaveText('exact')` / `.toHaveText(/regex/)`
- `await expect(locator).toContainText('partial')`
- `await expect(locator).toHaveCount(3)`
- `await expect(locator).toHaveValue('input value')`
- `await expect(locator).toBeEnabled()` / `.toBeDisabled()`
- `await expect(locator).toBeChecked()`
- `await expect(page).toHaveURL(/\/sales\/campañas\//)` ← page-level
- `await expect(page).toHaveTitle(/brand/i)`

Custom timeouts go on the matcher, not on a `waitFor`:

```typescript
await expect(page.getByText(/cargando/i)).toBeHidden({ timeout: 30_000 })
```

---

## 9. When a POM gets too big — split it

Heuristics for splitting:

- **> 12 methods** in one class → probably two pages or two phases of one page (split by tab/section)
- **> 200 LOC** → same as above
- **Methods that operate on disjoint locators** → separate concerns
- **One method that orchestrates 5+ others** → that method belongs in the spec, not the POM

Example: `BrandStudioPage` could split into `BrandStudioIdentityPage`, `BrandStudioStoryPage`, etc., once you have > 5 methods per tab.

---

## 10. Test ID conventions (when you must use them)

Sometimes there is no semantic role — a custom drawer, a gradient ribbon, a chart container. Use `data-testid`:

| Pattern | Example |
|---|---|
| `<feature>-<element>` | `data-testid="copilot-drawer"` |
| `<feature>-<element>-<index>` | `data-testid="kpi-card-revenue"` |
| `<feature>-<state>` | `data-testid="growth-stage-loading"` |

NEVER:
- Reuse the same testid across multiple components
- Embed user data: `data-testid="user-${user.id}"` (test will be tenant-specific)
- Make testids dynamic from props that change between renders

The FE component owns the testid. Co-locate it: when the FE component is renamed, the testid is renamed in the same diff.

---

## 11. POM lifecycle in a test

```
test starts
  ↓
auth.fixture provides `page` with token + tenant injected
  ↓
new MyPage(page)              ← cheap; just locator construction
  ↓
await myPage.goto(tenantId)   ← real network
  ↓
await myPage.expectLoaded()   ← web-first assert
  ↓
await myPage.doSomething()    ← user action
  ↓
await myPage.expectResult()   ← web-first assert
  ↓
test ends; browser context discarded
```

A new instance per test = isolation. Don't try to cache POMs across tests; the underlying browser context is gone.

---

## 12. POM smell test

Before merging a POM, ask:

- [ ] Could a non-tester read it and infer the page's behavior? (verbs are user-intents)
- [ ] Is every locator declared in the constructor? (no surprises in methods)
- [ ] Are all locators role/label/text-based? (no CSS, no XPath)
- [ ] Is every assertion in a dedicated `expect*()` method? (specs read clean)
- [ ] Does the POM avoid network/auth/state? (single responsibility)
- [ ] Are imports minimal? (only `Page`, `Locator`, `expect`)

If any answer is no, refactor before merging.
