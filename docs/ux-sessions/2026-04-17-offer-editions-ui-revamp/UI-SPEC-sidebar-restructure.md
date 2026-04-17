# UI-SPEC — Sidebar Restructure

> **Scope:** Agregar ítem "Inscripciones" bajo Closer Studio con badge NEW temporal.
>
> **Reference:** prototype sidebars en `prototype/sales/enrollments.html`.

## 1. Change scope

**Archivo a modificar:** `frontend/src/components/shared/layout/AppSidebar.tsx`

**Único cambio:** 1 ítem agregado bajo grupo `Closer Studio`.

## 2. Diff

```diff
 {
   title: "Closer Studio",
   href: `/${tenantId}/sales`,
   icon: CalendarCheck,
   children: [
     { title: "Resumen", href: `/${tenantId}/sales/resumen`, icon: LayoutDashboard },
     { title: "Studio", href: `/${tenantId}/sales/studio/inbox`, icon: Headset },
     { title: "Contactos", href: `/${tenantId}/sales/contactos`, icon: Users },
+    {
+      title: "Inscripciones",
+      href: `/${tenantId}/sales/enrollments`,
+      icon: ClipboardList,
+      badge: { label: "NEW", color: "accent", expiresAt: "2026-10-17" },
+    },
   ],
 },
```

## 3. Import agregar

```diff
 import {
   ...
+  ClipboardList,
   type LucideIcon,
 } from "lucide-react";
```

## 4. Extend types

### `NavChild` interface

```diff
 interface NavChild {
   title: string;
   href: string;
   icon: LucideIcon;
+  badge?: {
+    label: string;                      // "NEW", "BETA", etc.
+    color: 'accent' | 'success' | 'warning';
+    expiresAt?: string;                  // ISO date; after this date, badge hidden
+  };
 }
```

## 5. Render badge

### In `ExpandedGroupItem` children map

```diff
 <NavLink
   key={child.href}
   href={child.href}
   onClick={() => mobile && onMobileClose()}
   showLoadingIcon
   loadingClassName="opacity-70"
   className={cn(
     "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all relative group",
     isChildActive
       ? "text-primary bg-background shadow-sm border border-border/50"
       : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
   )}
 >
   {isChildActive && (
     <div className="absolute left-[-18px] w-[3px] h-[70%] bg-primary rounded-r-full" />
   )}
   <child.icon
     className={cn(
       "h-4 w-4 shrink-0",
       isChildActive
         ? "text-primary"
         : "text-muted-foreground group-hover:text-foreground",
     )}
   />
   {mounted && <span>{child.title}</span>}
+  {mounted && child.badge && isBadgeVisible(child.badge) && (
+    <span
+      className={cn(
+        "ml-auto text-[9px] font-semibold px-1.5 py-0.5 rounded-full uppercase",
+        badgeColorClasses(child.badge.color)
+      )}
+    >
+      {child.badge.label}
+    </span>
+  )}
 </NavLink>
```

### Helper functions

Agregar en el mismo archivo:

```ts
function isBadgeVisible(badge: NonNullable<NavChild['badge']>): boolean {
  if (!badge.expiresAt) return true;
  return new Date() < new Date(badge.expiresAt);
}

function badgeColorClasses(color: 'accent' | 'success' | 'warning'): string {
  switch (color) {
    case 'accent':
      return 'bg-primary text-primary-foreground';
    case 'success':
      return 'bg-emerald-100 text-emerald-700';
    case 'warning':
      return 'bg-amber-100 text-amber-700';
  }
}
```

## 6. Collapsed group item (flyout)

Cuando sidebar está colapsado y el usuario hover en Closer Studio, aparece un flyout con los children. También mostrar el badge allí:

```diff
 {(item.children ?? []).map((child) => {
   const isChildActive = pathname.startsWith(child.href);
   return (
     <NavLink
       key={child.href}
       href={child.href}
       loadingClassName="opacity-70"
       className={cn(
         "flex items-center gap-2 px-2 py-1.5 text-sm transition-colors",
         isChildActive ? "text-primary font-medium" : "text-foreground hover:bg-muted",
       )}
     >
       <child.icon className="h-4 w-4 shrink-0" />
       <span>{child.title}</span>
+      {child.badge && isBadgeVisible(child.badge) && (
+        <span
+          className={cn(
+            "ml-auto text-[9px] font-semibold px-1.5 py-0.5 rounded-full uppercase",
+            badgeColorClasses(child.badge.color)
+          )}
+        >
+          {child.badge.label}
+        </span>
+      )}
     </NavLink>
   );
 })}
```

## 7. Tests

### Vitest
`frontend/src/components/shared/layout/__tests__/AppSidebar.test.tsx` — agregar:

```ts
describe('Badge rendering', () => {
  it('shows NEW badge for Inscripciones before expiry', () => {
    // mock current date < 2026-10-17
    const { getByText } = render(<AppSidebar />);
    expect(getByText('Inscripciones')).toBeInTheDocument();
    expect(getByText('NEW')).toBeInTheDocument();
  });

  it('hides NEW badge after expiry', () => {
    vi.setSystemTime(new Date('2026-11-01'));
    const { queryByText } = render(<AppSidebar />);
    expect(queryByText('NEW')).not.toBeInTheDocument();
  });
});
```

## 8. Acceptance

- [x] Item "Inscripciones" visible bajo Closer Studio.
- [x] Badge NEW visible hasta 2026-10-17.
- [x] Click navega a `/[tenantId]/sales/enrollments`.
- [x] Item activo cuando pathname starts with `/sales/enrollments`.
- [x] Badge visible tanto en expanded sidebar como en collapsed flyout.
- [x] Badge desaparece automáticamente post-expiry.
- [x] Mobile sheet también muestra el badge.

## 9. References

- `frontend/src/components/shared/layout/AppSidebar.tsx` — archivo a modificar
- Lucide icon name: `ClipboardList` (Users también opción)
- Prototype: sidebar en `prototype/sales/enrollments.html`
