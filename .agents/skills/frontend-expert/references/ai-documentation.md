# AI-First Documentation Standards

To maximize the efficiency of AI agents (like Trae, Claude, Copilot) working on this codebase, all code must be documented with "AI Intent" in mind.

## 1. The "Why" over "What"
AI can read the code to know *what* it does. It needs comments to understand *why* it exists and *how* it fits into the larger system.

**Bad:**
```typescript
// Returns the user
function getUser(id: string) { ... }
```

**Good:**
```typescript
/**
 * [AI Context] Retrieves the full system user profile enriched with Tenant information.
 * Used primarily in the Dashboard Layout to determine permissions.
 * [Constraints] Returns 404 if the user is not linked to the current Tenant.
 */
function getUser(id: string) { ... }
```

## 2. Component Documentation
Every exported component in `src/features` or `src/components` MUST have a TSDoc block.

**Template:**
```typescript
/**
 * [Component Name]
 * [AI Context] Brief description of business purpose.
 * [Props] Key props that drive logic (optional if Typed clearly).
 * [UI Behavior] What user interaction does this handle? (e.g., "Opens modal on click").
 * [Dependencies] Key hooks or contexts used (e.g., "Requires AuthContext").
 */
```

**Example:**
```typescript
/**
 * BrandIdentityForm
 * [AI Context] Primary form for users to configure their AI Agent's persona (name, tone, style).
 * [UI Behavior] Auto-saves on blur; Blocks navigation if dirty.
 * [Dependencies] Uses useBrandSettings hook for persistence.
 */
export function BrandIdentityForm() { ... }
```

## 3. Hook Documentation
Custom hooks contain the "Brain" of the application. Document the state machine or logic flow.

**Template:**
```typescript
/**
 * [Hook Name]
 * [AI Context] What logic does this encapsulate?
 * [Input] Parameters.
 * [Output] Returned state and methods.
 * [Invariant] What condition is always true? (e.g., "isLoading is true until profile loads").
 */
```

## 4. "AI-Stop" Comments
If a specific block of code is fragile or has non-obvious edge cases, use an `AI-Stop` warning.

```typescript
// ! AI-STOP: Do not refactor this useEffect.
// The dependency array is intentionally empty to prevent infinite loops caused by
// the external widget's poor reference stability.
useEffect(() => { ... }, []);
```
