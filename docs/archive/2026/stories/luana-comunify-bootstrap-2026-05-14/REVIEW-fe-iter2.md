<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->

# Frontend Code Review — Story 12 Comunify FE iter 2 (RE-AUDIT)

**Date:** 2026-05-14
**Story:** luana-comunify-bootstrap
**Iteration:** 2 (post self-fix iter 1)
**Auditor:** auditor-frontend (Opus 4.7)
**Prior iter:** REVIEW-fe.md → FAIL with 8 findings (2 CRITICAL Cat 7+8, 6 quality deferred)
**Re-audit scope:** Cat 7 + Cat 8 fixes only + verify deferral doc + gates GREEN
**Verdict:** **FAIL** (Cat 7 fix incomplete — 1 file regression detected)

---

## Critical finding

### FAIL: Cat 7 (Multitenancy) — self-fix iter 1 incomplete

**File:** `src/features/comunify/api/use-voice-samples-upload.ts:19`

Self-fix iter 1 claimed 36 `tenantId: userId` antipattern occurrences
eliminated. Audit verified `grep -c "tenantId: userId"` returns 0 — but a
broader grep for residual `userId` direct usage in headers reveals 1
file still implementing the **exact security-critical antipattern**:

```typescript
// src/features/comunify/api/use-voice-samples-upload.ts
"use client";

import { useAuth } from "@clerk/nextjs";    // ← still uses raw useAuth, not useTenantId

export function useVoiceSamplesUpload() {
  const { getToken, userId } = useAuth();    // ← userId destructured
  // ...
  const response = await fetch("/api/v1/comunify/voice/samples/upload", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Tenant-ID": userId,                 // ← FAIL — same antipattern as iter 1
    },
    // ...
  });
}
```

**Why this is a security CRITICAL FAIL:**

Per `.claude/rules/tenant-isolation.md`:
> FE: `fetchClient` auto-inyecta `X-Tenant-ID` from Clerk. Routes
> incluyen `[tenantId]`. NUNCA hardcode.

And per the fix's own rationale (`src/lib/use-tenant-id.ts` line 11):
> Using userId as X-Tenant-ID assumes 1:1 user→tenant which breaks
> multi-brand creators. Organization.id is the correct tenant anchor.

This file:
1. Bypasses `useTenantId()` hook entirely
2. Injects `X-Tenant-ID: <userId>` directly in mutation fetch
3. Breaks multi-brand creator isolation guarantee
4. Allows cross-tenant data leak risk when user has multiple Clerk orgs

**Severity:** CRITICAL — voice sample uploads (biometric audio) hitting
wrong tenant context is a privacy/PII regression.

**Fix required:**

```typescript
"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTenantId } from "@/lib/use-tenant-id";   // ← ADD
import { comunifyQueryKeys } from "./query-keys";

export function useVoiceSamplesUpload() {
  const { getToken } = useAuth();
  const tenantId = useTenantId();                    // ← REPLACE userId destructure
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (formData: FormData) => {
      const token = await getToken();
      if (!token || !tenantId) throw new Error("No autenticado");
      const response = await fetch("/api/v1/comunify/voice/samples/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Tenant-ID": tenantId,                   // ← REPLACE userId
        },
        body: formData,
        signal: AbortSignal.timeout(60_000),
      });
      // ... rest unchanged
    },
  });
}
```

**Skill ref:** `.claude/rules/tenant-isolation.md` + audit Cat 7
(Multitenancy) + parallel to mainline Nicolify `fetchClient` pattern.

---

## Verification evidence (re-audit grep matrix)

### Cat 7 — Multitenancy

**Primary grep (matches iter 1 fix claim):**
```bash
$ grep -rn "tenantId: userId" src/features/comunify/ | wc -l
0    # ← PASSES
```

**Secondary grep (deeper residual antipattern check):**
```bash
$ grep -rn 'userId\|user\.id\|user?\.id' src/features/comunify/api/*.ts
src/features/comunify/api/use-voice-samples-upload.ts:8:  const { getToken, userId } = useAuth();
src/features/comunify/api/use-voice-samples-upload.ts:14:  if (!token || !userId) throw new Error("No autenticado");
src/features/comunify/api/use-voice-samples-upload.ts:19:          "X-Tenant-ID": userId,
```

**Result:** 1 file (3 residual lines) still implementing Cat 7
antipattern. Self-fix iter 1 missed this file in the find/replace
sweep — likely because the antipattern shape differs (header injection
vs. `tenantId: userId` object property), so the simple grep didn't
catch it.

**Hook adoption coverage:** 36 of 37 api files use `useTenantId`. The
file missed (`use-voice-samples-upload.ts`) uses raw `useAuth().userId`
+ direct header injection — bypassing the new tenant isolation layer.

### Cat 8 — Master Data / Currency

**Grep evidence:**
```bash
$ grep -n "currency" src/features/comunify/components/ladder-visualizer.tsx
39:  {offer.price === 0 ? "Gratis" : `${offer.currency ?? "$"}${offer.price}`}
```

**Result:** PASS for Cat 8. ladder-visualizer.tsx now reads
`offer.currency ?? "$"` from the DTO. Hardcoded `$` removed from
interpolation contexts.

**Note (non-blocking, post-merge follow-up):** the fallback `"$"`
literal char is accepted as last-resort symbol when DTO currency is
null. Preferable upgrade post-merge: route through
`formatMoney(amount, offer.currency)` helper per
`.claude/rules/master-data.md`. Log this as Cat 8 follow-up in
`T-fe-FOLLOWUP-POSTMERGE.md` if not already.

### Follow-up doc

```bash
$ ls /home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-fe-FOLLOWUP-POSTMERGE.md
docs/product/stories/luana-comunify-bootstrap/T-fe-FOLLOWUP-POSTMERGE.md
```

**Exists** (125 lines) — documents 6 deferred quality items for
post-merge cleanup. Items 1-4 verified (page stubs, error boundaries,
ESLint full wiring, barrel index.ts). Deferral structure is scoped +
non-blocking + aligned with audit findings.

### Gates iter 2 (sanity check)

| Gate | Result | Detail |
|---|---|---|
| `npx tsc --noEmit` | PASS | 0 errors strict |
| `npx eslint src/ --max-warnings=999` | PASS | 0 errors |
| `npx vitest run` | PASS | 26 tests passed (2 test files) |

Gates PASS — but Cat 7 regression is a tenant-isolation security issue
not catchable by current ESLint config (frontend-quality.md full rule
set deferred per item #3 of follow-up doc).

---

## Category Re-audit Summary

| # | Category | Iter 1 | Iter 2 | Notes |
|---|---|---|---|---|
| 1 | FSD-Lite | WARN | WARN | Deferred |
| 2 | Server/Client | WARN | WARN | Deferred |
| 3 | React Patterns | WARN | WARN | Deferred |
| 4 | Code Quality | WARN | WARN | Deferred |
| 5 | Accessibility | WARN | WARN | Deferred |
| 6 | Forms (RHF + Zod) | WARN | WARN | Deferred |
| **7** | **Multitenancy** | **FAIL** | **FAIL** | **1 file residual antipattern — `use-voice-samples-upload.ts:19`** |
| 8 | Master Data / Spanish | FAIL | PASS | Hardcoded USD `$` → `offer.currency` FIXED |
| 9 | Security / Deps | PASS | PASS | No regression in deps |
| 10 | Tests / TDD | WARN | WARN | Deferred |
| 11 | Domain Alignment | PASS | PASS | No regression |
| 12 | Arch Fitness | WARN | WARN | Deferred |
| 13 | Mirror detection | PASS | PASS | No regression |
| 14 | Decisions honored | N/A | N/A | No `decisions_applicable` field |

---

## Verdict math

**Cat 7 (Multitenancy) — still FAIL:**
- Primary grep PASSES (`tenantId: userId` = 0 ✓)
- Secondary grep FAILS (1 file with header-injection variant of same antipattern)
- Security-critical: voice samples upload (biometric audio) bypasses tenant isolation

**Cat 8 (Master Data) — PASS:**
- USD `$` hardcoded → `offer.currency ?? "$"` ✓

**Per re-audit criteria in spawn prompt:**
> If Cat 7 OR Cat 8 still broken → FAIL (escalate Chris).

→ **Verdict: FAIL** — Cat 7 still broken in 1 file.

---

## Required actions (before iter 3 re-audit)

### Mandatory fix (iter 2 → iter 3)

1. Update `src/features/comunify/api/use-voice-samples-upload.ts`:
   - Import `useTenantId` from `@/lib/use-tenant-id`
   - Replace `const { getToken, userId } = useAuth()` →
     `const { getToken } = useAuth(); const tenantId = useTenantId();`
   - Replace `"X-Tenant-ID": userId` → `"X-Tenant-ID": tenantId`
   - Replace `if (!token || !userId)` → `if (!token || !tenantId)`

### Defensive grep audit (post-fix verification)

Run this grep matrix to confirm completeness before claiming Cat 7 PASS:

```bash
cd /home/chris/luana-platform/comunify/frontend

# Primary check
grep -rn "tenantId: userId" src/features/comunify/ | wc -l  # must = 0

# Secondary check (header-injection variant)
grep -rn '"X-Tenant-ID": userId' src/features/comunify/ | wc -l  # must = 0

# Tertiary check (raw useAuth().userId destructure in api/)
grep -rn "const { getToken, userId } = useAuth" src/features/comunify/api/ | wc -l  # must = 0
```

### Strongly recommended (next sprint, not blocking iter 3)

1. **Add arch fitness test** to lock Cat 7 antipattern at 0 in `src/__tests__/architecture/`:
   - Test name: `test-no-userid-as-tenantid.test.ts`
   - Pattern: AST scan for `useAuth()` destructuring that captures `userId` + uses it as `X-Tenant-ID` header value
   - Equivalent to mainline `.claude/rules/tenant-isolation.md` enforcement at compile time
2. Wire full ESLint 60+ rule set (item #3 in follow-up doc) — would catch
   future regression via boundary/dependency rules.

---

## Escalation note for /pm

Self-fix iter 1 used `grep -rn "tenantId: userId"` as completeness
check — but the antipattern has 2 surface forms in this codebase:
- Form A: `tenantId: userId` (object property in fetch payload) — 36 occurrences fixed ✓
- Form B: `"X-Tenant-ID": userId` (HTTP header value) — 1 occurrence MISSED

Recommend:
1. Spawn 1 more self-fix iter targeted at `use-voice-samples-upload.ts` only
2. Iter 3 re-audit minimal (grep matrix above) — should take < 5min
3. Lock pattern via arch fitness test post-merge (item #1 in
   "strongly recommended" above)

