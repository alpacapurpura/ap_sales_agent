# UI-SPEC — Closer Studio (Enrollments page + Inbox widget)

> **Scope:** Nueva ruta `/sales/enrollments` + `EnrollmentWidget` integrado al inbox existente.
>
> **Reference prototype:** `prototype/sales/enrollments.html`, `prototype/sales/inbox.html`.

---

## 1. New route: `/sales/enrollments`

**File:** `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/enrollments/page.tsx`

**Title:** Inscripciones (Closer Studio)

### 1.1 Page structure

1. Header (title + subtitle + action buttons)
2. Global KPI strip (5 cards)
3. Rich filter bar
4. Warning banner (pending > 48h)
5. Grouped table por (oferta + edición)
6. Waitlist block

### 1.2 Header

```tsx
<header className="bg-white border-b border-slate-200 px-8 py-5">
  <div className="flex items-start justify-between">
    <div>
      <h1 className="text-2xl font-bold">Inscripciones</h1>
      <p className="text-sm text-slate-500 mt-0.5">
        Todos los leads que se inscribieron en cualquier oferta/cohorte. Operativo diario.
      </p>
    </div>
    <div className="flex gap-2">
      <Button variant="outline">⬇ Exportar</Button>
      <Button variant="primary">+ Crear manual</Button>
    </div>
  </div>
</header>
```

### 1.3 KPI strip

```tsx
<div className="grid grid-cols-5 gap-3 mb-5">
  <KpiCard label="Total inscripciones" value={total} />
  <KpiCard label="Pagadas este mes" value={paidThisMonth} color="emerald" />
  <KpiCard label="Pendientes de pago" value={pending} color="amber" subtext="Requieren follow-up" />
  <KpiCard label="En lista de espera" value={waitlistCount} color="purple" />
  <KpiCard label="Revenue total" value={formatMoney(revenue, currency)} />
</div>
```

### 1.4 Rich filter bar

```tsx
<div className="bg-white border border-slate-200 rounded-xl p-3 mb-4 flex flex-wrap items-center gap-2 text-xs">
  <FilterSelect label="Oferta" options={offers} value={offerFilter} onChange={setOfferFilter} />
  <FilterSelect label="Cohorte" options={editionsOf(offerFilter)} value={editionFilter} onChange={setEditionFilter} />
  <div className="flex items-center gap-1">
    <span className="text-slate-500">Estado:</span>
    <FilterPill active={status === 'all'}>Todas</FilterPill>
    <FilterPill active={status === 'paid'}>Pagadas</FilterPill>
    <FilterPill active={status === 'pending'}>Pendientes</FilterPill>
    <FilterPill active={status === 'waitlist'}>Waitlist</FilterPill>
    <FilterPill active={status === 'refunded'}>Reembolsadas</FilterPill>
  </div>
  <div className="ml-auto">
    <Input type="search" placeholder="Buscar…" value={query} onChange={setQuery} className="w-48" />
  </div>
</div>
```

### 1.5 Pending follow-up banner (conditional)

Si `pending > 48h` existe:
```tsx
<div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mb-4 flex items-center justify-between">
  <div className="flex items-center gap-2 text-sm">
    <span className="text-amber-700">⚠️</span>
    <span className="text-amber-900">
      <strong>{pendingOver48hCount} inscripciones</strong> con pago pendiente &gt; 48h · 
      el agente envió recordatorio, sin respuesta
    </span>
  </div>
  <Button variant="warning" size="sm" onClick={onOpenFollowupDrawer}>Ver + Reasignar</Button>
</div>
```

### 1.6 Grouped table

**Groups:** una "tarjeta-tabla" por `(oferta + edición)`, y un grupo extra "En lista de espera".

```tsx
<div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
  {groups.map(group => (
    <GroupSection
      key={group.key}
      label={group.label}
      count={group.enrollments.length}
      rightAction={group.isWaitlist
        ? <Button variant="primary" size="sm" onClick={() => onNotifyWaitlist(group)}>Notificar a todos</Button>
        : <Link href={`/offer-studio/offer/${group.offerId}?tab=ventas&edition=${group.editionId}`}>Ver cohorte →</Link>
      }
    >
      <EnrollmentsTable enrollments={group.enrollments} />
    </GroupSection>
  ))}
</div>
```

**GroupSection visual:**
```tsx
<div>
  <div className={cn(
    "border-b border-slate-200 px-4 py-2 flex items-center justify-between",
    isWaitlist ? "bg-purple-50 border-purple-200" : "bg-slate-50"
  )}>
    <span className={cn("text-sm font-semibold", isWaitlist ? 'text-purple-900' : '')}>
      {icon} {label} <span className={cn("font-normal ml-1", isWaitlist ? 'text-purple-600' : 'text-slate-500')}>({count})</span>
    </span>
    {rightAction}
  </div>
  <table>{children}</table>
</div>
```

### 1.7 EnrollmentsTable (inside group)

Mismo `EnrollmentRow` del `OfferVentasTab` (ver `UI-SPEC-offer-studio-tabs.md` § 2.4). Columnas:
- Contacto
- Estado
- Tier
- Monto
- Pagado
- Acciones

Para **waitlist group** la tabla tiene columnas diferentes:
- Contacto
- Esperó (días)
- Preferencia
- Acción (Asignar → Edición #X)

```tsx
<tr className="hover:bg-purple-50">
  <td className="p-3"><ContactCell contact={e.contact} /></td>
  <td className="p-3 text-xs text-slate-500">
    Esperó <strong>{daysSinceCreated}</strong> días · {e.offer.name} ({editionNounFor(e.offer)})
  </td>
  <td className="p-3 text-xs text-slate-500">
    {e.preference || 'Sin preferencia'}
  </td>
  <td className="p-3 text-right">
    <Popover>
      <PopoverTrigger><button className="text-xs text-purple-700">Asignar → Edición</button></PopoverTrigger>
      <PopoverContent>
        {publicEditionsOf(e.offer).map(ed => (
          <button key={ed.id} onClick={() => onAssign(e.id, ed.id)}>
            Edición #{ed.edition_number} · {formatMonth(ed.start_date)}
          </button>
        ))}
      </PopoverContent>
    </Popover>
  </td>
</tr>
```

### 1.8 Bulk notify action

Click "Notificar a todos" del waitlist group:
1. Confirm modal: "¿Notificar a {N} leads que la Edición #{X} ya está abierta?"
2. API call `POST /api/v1/sales-agent/enrollments/promote-waitlist` con `{enrollment_ids: allInWaitlistGroup, target_edition_id}`.
3. Toast con resumen: "N notificados · X errores".
4. Invalidate query.

---

## 2. Sidebar entry add

**File:** `frontend/src/components/shared/layout/AppSidebar.tsx`

Agregar dentro del grupo `Closer Studio`:

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
+      badge: { label: "NEW", color: "accent", expiresAt: "2026-10-17" }
+    },
   ],
 },
```

**Badge rendering:** extender `NavChild` interface y `ExpandedGroupItem`/`CollapsedGroupItem` con optional badge.

```diff
 interface NavChild {
   title: string;
   href: string;
   icon: LucideIcon;
+  badge?: {
+    label: string;
+    color: 'accent' | 'success' | 'warning';
+    expiresAt?: string;  // ISO date, after which badge disappears
+  };
 }
```

Render:
```tsx
{child.badge && (!child.badge.expiresAt || new Date() < new Date(child.badge.expiresAt)) && (
  <span className="ml-auto text-[9px] font-semibold px-1.5 py-0.5 rounded-full bg-accent text-accent-foreground uppercase">
    {child.badge.label}
  </span>
)}
```

---

## 3. EnrollmentWidget (in Inbox)

**File:** `frontend/src/features/closer-studio/components/EnrollmentWidget.tsx`

**Prototype:** `prototype/sales/inbox.html` right panel.

### 3.1 Integration point

Editar `frontend/src/features/sales/components/inbox/InboxSidePanel.tsx` (existe).

Agregar el widget después del "Contact card" y antes de otros paneles:

```tsx
<InboxSidePanel>
  <ContactCard contact={contact} />
  
  <EnrollmentWidget
    conversationId={conversation.id}
    offerId={activeEnrollment?.offer_id}
    editionId={activeEnrollment?.edition_id}
  />
  
  {/* existing panels */}
</InboxSidePanel>
```

### 3.2 Widget data

```ts
interface EnrollmentWidgetProps {
  conversationId: string;
}

// uses hook
const { enrollment, isLoading } = useActiveEnrollmentForConversation(conversationId);
// enrollment is Enrollment | null — null if no active enrollment for this conversation
```

### 3.3 Empty state

Si no hay enrollment activa para esta conversación:
```tsx
<Card>
  <CardHeader>
    <span className="text-xs font-semibold text-slate-500 uppercase">📝 Inscripción</span>
  </CardHeader>
  <CardContent className="text-center py-4">
    <p className="text-sm text-slate-600 mb-2">No hay inscripción activa para este contacto</p>
    <Button size="sm" variant="outline" onClick={onCreateEnrollmentManual}>
      + Crear inscripción manual
    </Button>
  </CardContent>
</Card>
```

### 3.4 Active enrollment visual

```tsx
<div className="bg-white border-2 border-blue-200 rounded-xl overflow-hidden ring-1 ring-blue-100">
  <div className="bg-blue-50 border-b border-blue-100 px-3 py-2 flex items-center justify-between">
    <span className="text-xs font-semibold text-blue-700 uppercase">📝 Inscripción activa</span>
    <span className="badge-new">NEW</span>
  </div>
  
  <div className="p-3 space-y-3 text-sm">
    {/* Offer + Edition row */}
    <div className="flex items-center gap-2">
      <OfferIcon icon={offer.icon_name} />
      <div className="flex-1 min-w-0">
        <p className="font-semibold truncate">{offer.name}</p>
        <p className="text-xs text-slate-500">
          {edition
            ? `Edición #${edition.edition_number} · ${formatDate(edition.start_date)}`
            : 'En lista de espera · sin edición asignada'
          }
        </p>
      </div>
    </div>
    
    {/* Status + Tier + Link info */}
    <div className="bg-slate-50 rounded-lg p-2.5 space-y-1.5 text-xs">
      <div className="flex justify-between">
        <span className="text-slate-500">Estado</span>
        <EnrollmentStatusBadge status={enrollment.status} />
      </div>
      {enrollment.pricing_tier_label && (
        <div className="flex justify-between">
          <span className="text-slate-500">Tier</span>
          <span className="font-semibold">{enrollment.pricing_tier_label} · {formatMoney(enrollment.pricing_amount, enrollment.currency)}</span>
        </div>
      )}
      {enrollment.payment_link_url && enrollment.status === 'payment_pending' && (
        <div className="flex justify-between">
          <span className="text-slate-500">Link enviado</span>
          <span>{formatRelative(enrollment.created_at)}</span>
        </div>
      )}
      {enrollment.paid_at && (
        <div className="flex justify-between">
          <span className="text-slate-500">Pagado</span>
          <span>{formatRelative(enrollment.paid_at)}</span>
        </div>
      )}
    </div>
    
    {/* Action buttons (depend on status) */}
    <div className="flex gap-1.5">
      {enrollment.status === 'payment_pending' && (
        <>
          <Button variant="outline" size="xs" className="flex-1" onClick={onResendLink}>
            🔗 Reenviar link
          </Button>
          <Button variant="outline" size="xs" className="flex-1" onClick={onMarkPaid}>
            ✓ Marcar pagada
          </Button>
        </>
      )}
      {enrollment.status === 'paid' && (
        <Button variant="outline" size="xs" className="flex-1" onClick={onMarkAttended}>
          🎓 Marcar asistida
        </Button>
      )}
      {enrollment.status === 'intent' && (
        <Button variant="primary" size="xs" className="flex-1" onClick={onGeneratePaymentLink}>
          🔗 Generar link de pago
        </Button>
      )}
    </div>
    
    {/* Deep link */}
    <Link
      href={editionId
        ? `/offer-studio/offer/${offer.id}?tab=ventas&edition=${edition.id}`
        : `/sales/enrollments?offer_id=${offer.id}&status=waitlist`
      }
      className="block text-center text-xs text-blue-600 font-medium hover:underline"
    >
      Ver en la cohorte →
    </Link>
  </div>
</div>
```

### 3.5 Status-specific actions

| Status | Actions visibles |
|---|---|
| INTENT | [Generar link de pago] |
| WAITLIST | [Ver waitlist] |
| PAYMENT_PENDING | [Reenviar link] [Marcar pagada] |
| PAID | [Marcar asistida] [Ver factura] |
| ATTENDED | [Ver certificado] |
| REFUNDED | (read-only, no actions) |
| CANCELLED | (read-only, no actions) |

---

## 4. Hooks

### 4.1 `use-enrollments.ts`

```ts
export function useEnrollments(filters: EnrollmentFilters) {
  return useQuery({
    queryKey: ["enrollments", filters],
    queryFn: () => enrollmentsApi.list(filters),
    staleTime: 60 * 1000,
  });
}
```

### 4.2 `use-active-enrollment-for-conversation.ts`

```ts
export function useActiveEnrollmentForConversation(conversationId: string) {
  return useQuery({
    queryKey: ["enrollment", "by-conversation", conversationId],
    queryFn: () => enrollmentsApi.getByConversation(conversationId),
    enabled: !!conversationId,
    staleTime: 30 * 1000,
  });
}
```

### 4.3 `use-promote-waitlist.ts`

```ts
export function usePromoteWaitlist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PromoteWaitlistPayload) => enrollmentsApi.promoteWaitlist(payload),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["enrollments"] });
      toast.success(`${result.promoted} notificados · ${result.failed} errores`);
    },
  });
}
```

---

## 5. API client

**File:** `frontend/src/features/closer-studio/api/enrollments-api.ts`

```ts
export const enrollmentsApi = {
  list: (filters: EnrollmentFilters, token: string): Promise<Enrollment[]> => ...,
  getByConversation: (conversationId: string, token: string): Promise<Enrollment | null> => ...,
  resendPaymentLink: (enrollmentId: string, token: string): Promise<Enrollment> => ...,
  markPaid: (enrollmentId: string, token: string): Promise<Enrollment> => ...,
  markAttended: (enrollmentId: string, token: string): Promise<Enrollment> => ...,
  generatePaymentLink: (enrollmentId: string, token: string): Promise<{ url: string }> => ...,
  promoteWaitlist: (payload: PromoteWaitlistPayload, token: string): Promise<{ promoted: number; failed: number }> => ...,
};
```

---

## 6. Test scenarios

### 6.1 EnrollmentsPage tests
- Render empty state cuando no hay enrollments.
- Render con 3 groups (2 offers + 1 waitlist).
- Filter by offer: groups se filtran.
- Filter by status: filas se filtran dentro de grupos.
- Bulk notify: llama API + invalidate + toast.
- Assign waitlist to edition: popover abre, click → API → row desaparece.

### 6.2 EnrollmentWidget tests
- Empty state cuando no hay enrollment activa.
- Render con status INTENT → "Generar link" action.
- Render con status PAYMENT_PENDING → "Reenviar" + "Marcar pagada" actions.
- Render con status PAID → "Marcar asistida" action.
- Resend link: click → API → toast success.

### 6.3 E2E smoke
`frontend/e2e/specs/smoke/closer-enrollments.spec.ts`:
- Navegar a `/sales/enrollments`.
- Verificar KPIs visibles.
- Verificar al menos 1 grupo con al menos 1 fila.
- Click en "Chat →" navega a inbox con conversationId.

`frontend/e2e/specs/regression/enrollment-widget.spec.ts`:
- Abrir inbox con conversación que tenga enrollment.
- Verificar widget visible en side panel.
- Click "Reenviar link" → verificar toast.

---

## 7. Implementation checklist

- [ ] Route `/sales/enrollments/page.tsx` + `EnrollmentsPage.tsx`
- [ ] `GroupSection.tsx` + `EnrollmentRow.tsx` (shared con `OfferVentasTab`)
- [ ] `WaitlistRow.tsx` con assign popover
- [ ] Rich filter bar: offer select + edition select (cascading) + status pills + search
- [ ] Follow-up warning banner (conditional)
- [ ] Bulk notify with confirm modal
- [ ] `EnrollmentWidget.tsx` con 7 state variants
- [ ] Integration en `InboxSidePanel.tsx`
- [ ] Hooks: useEnrollments, useActiveEnrollmentForConversation, usePromoteWaitlist, useResendPaymentLink, useMarkPaid, useMarkAttended
- [ ] API client `enrollments-api.ts`
- [ ] Sidebar badge entry agregado
- [ ] Vitest tests por component
- [ ] E2E smoke + regression

---

## 8. References

- Prototype HTML: `docs/ux-sessions/2026-04-17-offer-editions-ui-revamp/prototype/sales/`
- Enrollment backend entity (Phase 5 pending): `FLOW-SPEC.md` § 8
- Existing inbox: `frontend/src/features/sales/components/inbox/` (ya existe, se extiende)
