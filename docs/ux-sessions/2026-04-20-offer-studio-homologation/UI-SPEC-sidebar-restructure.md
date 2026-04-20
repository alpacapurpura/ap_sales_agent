# UI-SPEC — Sidebar (no change required)

**Status:** no-op
**Scope:** Nicolify global sidebar (`components/shared/layout/AppSidebar.tsx`)

---

## Assessment

Current entry for Offer Studio points to `/{tenantId}/offer-studio` — **already correct**.
No label change, no icon change, no reorder required.

## Verification

```bash
grep -n "offer-studio" frontend/src/components/shared/layout/AppSidebar.tsx
# expected:
#   href: `/${tenantId}/offer-studio`,
```

## Deletion from sidebar considerations

- `/offer-studio/interview` was never in global sidebar (correctly scoped to studio-internal). Removing that route does not affect sidebar.

## Conclusion

No UI change to global sidebar needed. Listed here as a delta spec for completeness — `nicolify-frontend` can skip this file and focus on shell + copilot specs.
