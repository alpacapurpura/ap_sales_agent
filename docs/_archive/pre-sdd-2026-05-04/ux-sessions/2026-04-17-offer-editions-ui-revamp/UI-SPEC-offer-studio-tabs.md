# UI-SPEC — Offer Studio Tabs (Info, Ventas, Assets, Campañas)

> **Scope:** Contenido de cada uno de los 4 tabs del OfferShell.
>
> **Reference prototype:** `prototype/offer-studio/offer-info.html`, `offer-ventas.html`, `offer-assets.html`, `offer-campanas.html`.
>
> **Related:** `UI-SPEC-offer-studio-shell.md` (el shell que contiene estos tabs).

---

## 1. Tab — Info (default)

**File:** `frontend/src/features/offer-studio/components/info/OfferInfoTab.tsx`

**Prototype:** `prototype/offer-studio/offer-info.html` § "Info content".

### 1.1 Structure

7 secciones en orden vertical, todas editables inline:

1. **Identidad** — nombre, archetype, promesa
2. **Fechas y Logística** (edition-scoped) — start/end/registration dates, location, formato, capacidad
3. **Precios y Escalera** (edition-scoped) — pricing tiers con timeline visual
4. **Entregables** — list items con format + quantity
5. **Público** — avatars + capacidad financiera + prerequisitos
6. **Garantía y Onboarding** — tipo + detalle
7. **Conocimiento (RAG del agente)** — file uploader + list indexed

### 1.2 Para offer SIN ediciones (PRODUCTO / MEMBRESIA)

- Sección 2 se renombra a **Acceso y Entrega** (sin fechas): formato, duración de acceso, fulfillment, onboarding.
- Sección 3 se reduce a **Precio único** (sin pricing tiers timeline).

### 1.3 Section component pattern

Cada sección es un `<Card>` con header (título + estado completeness) + body (fields).

```tsx
<SectionCard
  title="2. Fechas y Logística"
  subtitle="Específico de Edición #3"
  status="complete" | "incomplete" | "readonly"
  onEdit={() => setEditMode(true)}
>
  {isEditMode ? <FormFields /> : <ReadonlyFields />}
</SectionCard>
```

**Header visual:**
```tsx
<header className="flex items-center justify-between mb-3">
  <div>
    <h3 className="font-semibold">{title}</h3>
    {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
  </div>
  <CompletenessBadge status={status} />
</header>
```

**CompletenessBadge:**
- `complete`: `<span class="text-xs text-emerald-600">✓ Completa</span>`
- `incomplete`: `<span class="text-xs text-amber-600">⚠ Pendiente</span>`
- `readonly`: `<span class="text-xs text-slate-400">🔒 Solo lectura</span>`

### 1.4 Section 1 — Identidad

Fields:
- `offer.public_name` (string, required) — tilted toward current edition naming convention ("MasterClass de Copywriting — Jul 2026")
- `offer.archetype` (readonly, shown as label "Programa · DWY")
- `offer.headline_promise` (textarea, full width)

Read-only display: 3 campos en grid 2 cols, promise span-2.

### 1.5 Section 2 — Fechas y Logística (edition-scoped)

Fields:
- `edition.start_date` (datetime-local)
- `edition.end_date` (datetime-local, optional)
- `edition.registration_start` (datetime-local, optional)
- `edition.registration_end` (datetime-local, optional)
- `edition.timezone` (select — IANA zones)
- `edition.capacity` (number, optional)
- `edition.location_override.format` (select: virtual/presencial/hybrid)
- `edition.location_override.platform` (string, if virtual: "Zoom", "Discord", etc.)
- `edition.language` (select: es/en/pt)

Visual (readonly):
```tsx
<div className="grid grid-cols-2 gap-4 text-sm">
  <Field label="Inicio">{formatFullDate(edition.start_date)} · {formatTime(edition.start_date)}</Field>
  <Field label="Fin">{formatFullDate(edition.end_date)}</Field>
  <Field label="Inscripciones">{formatDate(reg_start)} → {formatDate(reg_end)}</Field>
  <Field label="Capacidad">
    {edition.capacity} · <span className="text-emerald-600">{enrolled} inscriptos ({enrolledPct}%)</span>
  </Field>
  <Field label="Formato">{location.format} · {location.platform}</Field>
  <Field label="Idioma">{displayLanguage(edition.language)}</Field>
</div>
```

### 1.6 Section 3 — Precios y Escalera (edition-scoped)

**Timeline visual** (reusa `.tier-timeline` del prototipo):

```tsx
<div className="mb-2 text-[10px] text-slate-500 flex justify-between">
  <span>{formatShortDate(firstTierStart)}</span>
  <span>{formatShortDate(secondTierStart)}</span>
  <span>{formatShortDate(lastTierStart)}</span>
  <span>Inicio {formatShortDate(edition.start_date)}</span>
</div>
<div className="tier-timeline mb-4">
  {tiers.map((tier, i) => (
    <div
      key={tier.label}
      className={cn("tier-segment", `tier-${tier.label}`)}
      style={{
        left: `${calcPosition(tier.valid_from, minDate, maxDate)}%`,
        width: `${calcWidth(tier.valid_from, tier.valid_until, minDate, maxDate)}%`,
      }}
    >
      {tier.label} · {formatMoney(tier.pricing[0].total_amount, currency)}
    </div>
  ))}
</div>
```

**Tier rows** (lista + editor):

```tsx
<div className="space-y-1.5 text-sm">
  {tiers.map(tier => (
    <TierRow key={tier.label} tier={tier} isActive={tier === activeTier} onEdit={...} />
  ))}
</div>
```

TierRow read-only:
```tsx
<div className={cn(
  "flex items-center gap-3 p-2.5 border rounded",
  isActive ? "border-emerald-200 bg-emerald-50/40" : "border-slate-200 text-slate-600"
)}>
  <div className={`w-3 h-3 rounded-full tier-${tier.label}`}></div>
  <span className="font-semibold">{tier.label_es}</span>
  <span className="flex-1 text-xs text-slate-500">
    {formatDate(tier.valid_from)} → {formatDate(tier.valid_until)}
  </span>
  <span className="font-bold">{formatMoney(tier.pricing[0].total_amount, currency)}</span>
  {isActive && <span className="text-xs text-emerald-700 font-semibold">● Activo</span>}
</div>
```

### 1.7 Section 4 — Entregables

List dinámico de `DeliverableItem`:
```tsx
<ul className="text-sm space-y-1">
  {deliverables.map(d => (
    <li key={d.name}>✓ {d.name} <span className="text-slate-400">({d.quantity})</span></li>
  ))}
</ul>
```

Edit mode: CRUD table con `name`, `format` (select), `quantity`, `value_stack_price`.

### 1.8 Section 5 — Público

```tsx
<div className="flex flex-wrap gap-1 mb-2">
  {offer.target_avatar_match.map(avatar => (
    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">{avatarLabel(avatar)}</span>
  ))}
</div>
<p className="text-xs text-slate-500">
  Capacidad financiera: {offer.min_financial_capacity} · 
  Prerequisito: {displayPrerequisites(offer.prerequisites)}
</p>
```

### 1.9 Section 6 — Garantía y Onboarding

```tsx
<div className="grid grid-cols-2 gap-4 text-sm">
  <Field label="Garantía">{guaranteeLabel(offer.guarantee_type)}</Field>
  <Field label="Onboarding">{onboardingLabel(offer.onboarding_mechanism)}</Field>
</div>
```

### 1.10 Section 7 — Conocimiento (RAG)

File list + upload CTA:
```tsx
<div className="space-y-1.5 text-sm">
  {knowledgeSources.map(source => (
    <KnowledgeSourceRow
      key={source.id}
      source={source}
      onDelete={...}
    />
  ))}
  <KnowledgeUploadCTA onFileAdd={...} onUrlAdd={...} />
</div>
```

KnowledgeSourceRow:
```tsx
<div className="flex items-center justify-between p-2 border border-slate-200 rounded bg-slate-50">
  <span className="flex items-center gap-2">
    {fileIcon(source.source_type)} {source.file_name}
    <span className="text-xs text-slate-400">· {formatBytes(source.size)}</span>
  </span>
  <KnowledgeStatusBadge status={source.status} />
</div>
```

KnowledgeStatusBadge:
- `queued`: amber "En cola"
- `processing`: amber "Procesando..."
- `indexed`: emerald "● Indexado"
- `error`: red "● Error"

### 1.11 Pending banner

Si alguna sección tiene status `incomplete`:
```tsx
<div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
  <span className="w-8 h-8 rounded-full bg-amber-200 text-amber-700 flex items-center justify-center">⚠</span>
  <div className="flex-1">
    <p className="text-sm font-semibold text-amber-900">{pendingCount} secciones pendientes</p>
    <p className="text-xs text-amber-700">{pendingList.join(' · ')} — el agente los usará para responder</p>
  </div>
  <Button onClick={onAutoCompleteAI} size="sm" variant="warning">Autocompletar con IA</Button>
</div>
```

---

## 2. Tab — Ventas

**File:** `frontend/src/features/offer-studio/components/ventas/OfferVentasTab.tsx`

**Prototype:** `prototype/offer-studio/offer-ventas.html`.

### 2.1 Structure

1. KPI strip (5 cards)
2. Filter pills (estado)
3. Enrollments table
4. Closer Studio deep-link banner

### 2.2 KPI strip

```tsx
<div className="grid grid-cols-5 gap-3">
  <KpiCard label="Inscriptos" value={enrolled} subtext={`de ${capacity} · ${pct}%`} />
  <KpiCard label="Pagados" value={paid} color="emerald" />
  <KpiCard label="Pend. pago" value={pending} color="amber" />
  <KpiCard label="Revenue" value={formatMoney(revenue, currency)} />
  <KpiCard label="Waitlist" value={waitlistCount} color="purple" />
</div>
```

### 2.3 Filter pills

```tsx
<div className="flex items-center gap-2 text-xs">
  <span className="text-slate-500">Estado:</span>
  <FilterPill active={filter === 'all'} onClick={() => setFilter('all')}>Todas ({total})</FilterPill>
  <FilterPill active={filter === 'paid'} onClick={() => setFilter('paid')}>Pagadas ({paid})</FilterPill>
  <FilterPill active={filter === 'pending'} onClick={() => setFilter('pending')}>Pendientes ({pending})</FilterPill>
  <span className="ml-3 text-slate-300">·</span>
  <FilterPill active={filter === 'meeting_closes'} onClick={() => setFilter('meeting_closes')}>Cierres por reunión</FilterPill>
</div>
```

### 2.4 Enrollments table

**Columns:** Contacto · Estado · Tier · Monto · Pagado · Acciones.

```tsx
<table className="w-full text-sm">
  <thead className="bg-slate-50 border-b border-slate-200 text-xs text-slate-500">
    <tr>
      <th className="text-left p-3 font-medium">Contacto</th>
      <th className="text-left p-3 font-medium">Estado</th>
      <th className="text-left p-3 font-medium">Tier</th>
      <th className="text-left p-3 font-medium">Monto</th>
      <th className="text-left p-3 font-medium">Pagado</th>
      <th className="text-right p-3 font-medium"></th>
    </tr>
  </thead>
  <tbody className="divide-y divide-slate-100">
    {enrollments.map(e => <EnrollmentRow key={e.id} enrollment={e} />)}
  </tbody>
</table>
```

**EnrollmentRow:**
```tsx
<tr className={cn("hover:bg-slate-50", e.status === 'payment_pending' && 'bg-amber-50/30')}>
  <td className="p-3">
    <div className="flex items-center gap-2">
      <Avatar initials={initials(e.contact.name)} colorSeed={e.contact.id} />
      <div>
        <div className="font-medium">{e.contact.name}</div>
        <div className="text-xs text-slate-500">
          {e.status === 'payment_pending' && daysSinceLinkSent > 2
            ? <span className="text-amber-700">⚠ {daysSinceLinkSent} días sin pagar</span>
            : e.contact.email
          }
        </div>
      </div>
    </div>
  </td>
  <td className="p-3"><EnrollmentStatusBadge status={e.status} /></td>
  <td className="p-3 text-xs">{e.pricing_tier_label || '—'}</td>
  <td className="p-3 font-semibold">{formatMoney(e.pricing_amount, e.currency)}</td>
  <td className="p-3 text-xs text-slate-500">{e.paid_at ? formatDate(e.paid_at) : '—'}</td>
  <td className="p-3 text-right">
    {e.status === 'payment_pending'
      ? <button className="text-xs text-amber-600 hover:underline" onClick={() => onResendLink(e)}>Reenviar link</button>
      : <a href={`/sales/studio/inbox?conversationId=${e.conversation_id}`} className="text-xs text-blue-600 hover:underline">Chat →</a>
    }
  </td>
</tr>
```

**EnrollmentStatusBadge:**
| Status | Label | Color |
|---|---|---|
| INTENT | "💭 Intención" | slate |
| WAITLIST | "📋 Waitlist" | purple |
| PAYMENT_PENDING | "⏳ Pendiente" | amber |
| PAID | "✓ Pagada" | emerald |
| ATTENDED | "🎓 Asistió" | blue |
| REFUNDED | "↩ Reembolsada" | red |
| CANCELLED | "✕ Cancelada" | slate 400 |

### 2.5 Closer Studio deep-link banner

```tsx
<div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between">
  <div className="flex items-center gap-3">
    <span className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center">🎯</span>
    <div>
      <p className="text-sm font-semibold text-blue-900">¿Necesitás más detalle por inscripción?</p>
      <p className="text-xs text-blue-700">Ver conversaciones completas, timeline, payment attempts y gestión operativa en Closer Studio.</p>
    </div>
  </div>
  <Link href={`/sales/enrollments?offer_id=${offerId}&edition_id=${currentEditionId}`}>
    <Button>Ir a Closer Studio →</Button>
  </Link>
</div>
```

---

## 3. Tab — Assets (placeholder for Canva-clone)

**File:** `frontend/src/features/offer-studio/components/assets/OfferAssetsTab.tsx`

**Prototype:** `prototype/offer-studio/offer-assets.html`.

### 3.1 Structure

1. Placeholder banner (fase 2 coming soon)
2. Action bar: filter pills + "Jalar de Edición #N" + "Generar con IA"
3. Gallery grid (tiles)
4. Informational footnote

### 3.2 Placeholder banner

```tsx
<div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center justify-between">
  <div className="flex items-center gap-3">
    <span className="w-10 h-10 rounded-full bg-amber-200 text-amber-700 flex items-center justify-center">🚧</span>
    <div>
      <p className="text-sm font-semibold text-amber-900">Editor visual tipo Canva — Próximamente</p>
      <p className="text-xs text-amber-700">Generación con IA + edición inline de flyers, reels, carruseles y anuncios. Por ahora ves los assets existentes y subís manualmente.</p>
    </div>
  </div>
  <span className="text-xs text-amber-700 font-semibold">Fase 2</span>
</div>
```

### 3.3 Action bar

```tsx
<div className="flex items-center justify-between">
  <div className="flex items-center gap-2 text-xs">
    <FilterPill active={type === 'all'}>Todos ({total})</FilterPill>
    <FilterPill active={type === 'flyer'}>Flyers ({flyers})</FilterPill>
    <FilterPill active={type === 'video'}>Reels ({videos})</FilterPill>
    <FilterPill active={type === 'carousel'}>Carruseles ({carousels})</FilterPill>
    <FilterPill active={type === 'document'}>Documentos ({docs})</FilterPill>
  </div>
  <div className="flex gap-2">
    <Button variant="outline" onClick={onOpenAssetCloneModal}>📥 Jalar de Edición #N</Button>
    <Button variant="primary" onClick={onGenerateWithAI}>+ Generar con IA</Button>
  </div>
</div>
```

### 3.4 Gallery grid

```tsx
<div className="grid grid-cols-5 gap-3">
  {assets.map(asset => (
    <AssetTile key={asset.id} asset={asset} onClick={() => openCanvaStub(asset)} />
  ))}
</div>
```

**AssetTile:**
```tsx
<button
  className="asset-tile hover:ring-2 hover:ring-blue-400 cursor-pointer"
  title="Click abre editor Canva-like en nueva pestaña"
>
  {asset.shared_across_editions && <span className="badge-scope" style={{background: '#eff6ff', color: '#1d4ed8'}}>Compartido</span>}
  <span>{typeIcon(asset.type)} {asset.label}</span>
</button>
```

**Click behavior (stub for Phase 2):**
```ts
function openCanvaStub(asset: OfferAsset) {
  window.open(`/offer-studio/offer/${offerId}/editions/${editionId}/assets/${asset.id}/edit`, '_blank');
  // Stub page shows "Editor Canva-clone · Próximamente" message + asset preview.
}
```

### 3.5 Footnote

```tsx
<p className="mt-4 text-xs text-slate-500 italic">
  💡 Hacer click en un asset abre el editor Canva-clone en una nueva pestaña. Los assets se generan automáticamente cuando se crea la edición (desde template o clonando la anterior), el usuario edita detalles menores.
</p>
```

### 3.6 Reuse existing AssetCloneModal

`frontend/src/features/offer-studio/components/assets/AssetCloneModal.tsx` ya existe (de Phase 3). Lo reutilizamos acá. Ver UI-SPEC-offer-studio-shell.md si necesita cambios visuales.

---

## 4. Tab — Campañas

**File:** `frontend/src/features/offer-studio/components/campanas/OfferCampanasTab.tsx`

**Prototype:** `prototype/offer-studio/offer-campanas.html`.

### 4.1 Structure

1. Explainer banner ("acá ves asociadas, config avanzada en Growth")
2. KPI strip
3. Section: campañas list
4. Orgánico/email placeholder footer

### 4.2 Explainer banner

```tsx
<div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between">
  <div className="flex items-center gap-3">
    <span className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center">📊</span>
    <div>
      <p className="text-sm font-semibold text-blue-900">Acá ves solo las campañas asociadas a esta edición</p>
      <p className="text-xs text-blue-700">La configuración avanzada y analítica vive en Growth Studio. Desde acá linkeás campañas existentes o creás nuevas.</p>
    </div>
  </div>
  <Link href={`/growth-studio/ventas?offer_id=${offerId}`}>
    <Button>Ir a Growth Studio →</Button>
  </Link>
</div>
```

### 4.3 KPI strip (4 cards)

```tsx
<div className="grid grid-cols-4 gap-3">
  <KpiCard label="Campañas activas" value={activeCampaigns} />
  <KpiCard label="Inversión" value={formatMoney(totalSpend, currency)} subtext="últimos 30 días" />
  <KpiCard label="Leads generados" value={totalLeads} />
  <KpiCard label="ROAS estimado" value={`${roas.toFixed(1)}x`} />
</div>
```

### 4.4 Campaign cards list

```tsx
<div className="space-y-3">
  {campaigns.map(c => <CampaignCard key={c.id} campaign={c} />)}
</div>
```

**CampaignCard:**
```tsx
<div className="bg-white border border-slate-200 rounded-xl p-4 flex items-start gap-4">
  <PlatformIcon platform={c.platform} />
  <div className="flex-1 min-w-0">
    <div className="flex items-center gap-2 mb-1">
      <p className="font-semibold">{c.name}</p>
      <PlatformBadge platform={c.platform} />
      <CampaignStatusBadge status={c.status} />
    </div>
    <p className="text-xs text-slate-500 mb-3">
      Flight {formatDate(c.start)} → {formatDate(c.end)} · {c.ad_sets_count} ad sets · {c.ads_count} anuncios
    </p>
    <div className="grid grid-cols-4 gap-3 text-xs">
      <KpiInline label="Inversión" value={formatMoney(c.spend, currency)} />
      <KpiInline label={c.platform === 'google' ? 'Clicks' : 'Leads'} value={c.leads} />
      <KpiInline label={c.platform === 'google' ? 'CPC' : 'CPA'} value={formatMoney(c.cpa, currency)} />
      <KpiInline label="Inscripciones atribuidas" value={c.attributed_enrollments} color="emerald" />
    </div>
  </div>
  <div className="flex flex-col items-end gap-1">
    <Link href={`/growth-studio/ventas?campaign_id=${c.id}`} className="text-xs text-blue-600 hover:underline whitespace-nowrap">
      Ver en Growth →
    </Link>
    <button className="text-xs text-slate-400 hover:text-slate-800" onClick={() => showCampaignOptions(c)}>⋮</button>
  </div>
</div>
```

**PlatformIcon:** 48×48 rounded-lg, color per platform:
- Meta: bg-blue-100 text-blue-600, icon Ⓜ o `<Facebook />`
- Google: bg-amber-100 text-amber-600, icon G
- YouTube: bg-red-100 text-red-600, icon ▶
- TikTok: bg-slate-900 text-white, icon 🎵
- Instagram: bg-pink-100 text-pink-600, icon 📷

**PlatformBadge:** text-xs px-2 py-0.5 rounded background per platform.

**CampaignStatusBadge:**
| Status | Label | Color |
|---|---|---|
| ACTIVE | "● Activa" | emerald |
| PAUSED | "⏸ Pausada" | slate |
| SCHEDULED | "⏰ Programada" | amber |
| ENDED | "✓ Finalizada" | slate |
| ERROR | "⚠ Error" | red |

### 4.5 Associate button (top of section)

```tsx
<div className="flex items-center justify-between">
  <h3 className="text-sm font-semibold">Campañas asociadas ({campaigns.length})</h3>
  <Button variant="outline" onClick={openAssociatePicker}>+ Asociar campaña existente</Button>
</div>
```

**Associate picker** = modal con lista de campañas no-asociadas fetcheadas de Growth Studio API. Click en una → llama `POST /api/v1/growth-studio/campaigns/{id}/associate-offer` con `{offer_id, edition_id}`.

### 4.6 Orgánico/email placeholder

```tsx
<div className="bg-slate-100 border border-slate-200 rounded-xl p-4">
  <p className="text-sm font-semibold mb-1">💡 ¿También usás email o IG orgánico para promocionar?</p>
  <p className="text-xs text-slate-600 mb-3">Por ahora Campañas lista solo ads pagos (Meta / Google / YouTube / TikTok). Email sequences y posts orgánicos los verás pronto en una pestaña "Canales" — o configurálos desde Growth Studio.</p>
  <div className="flex gap-2">
    <Button variant="outline" size="sm">📧 Configurar email sequence</Button>
    <Button variant="outline" size="sm">📱 Configurar posts IG</Button>
  </div>
</div>
```

---

## 5. Routing behavior (shared by all tabs)

### 5.1 URL pattern
```
/[tenantId]/offer-studio/offer/[id]?tab={tab}&edition={editionId}
```

- `tab` optional, default `info`.
- `edition` optional, default = edición activa (computed: próxima si existe, else active, else última pasada).

### 5.2 Tab change
- Next.js router `push` (nueva entry en history).
- Data re-fetch scoped a `tab + edition` combination.
- Rail highlight remains as-is (edition unchanged).

### 5.3 Edition change via rail
- Next.js router `replace` (no nueva entry).
- Data re-fetch scoped a new edition.
- Tab active se mantiene.
- Scroll a top del main content (reset por edición switch).

### 5.4 Deep link behavior
- User shares URL `/offer/abc?tab=ventas&edition=xyz` → al abrir, Ventas activo con edición xyz seleccionada.
- Si `edition` inválido/eliminado → fallback a edición activa, toast warning "Edición no disponible, mostrando {X}".

---

## 6. Data fetching patterns

### 6.1 Hooks
```ts
useOffer(offerId)                                 // offer data (shared)
useEditions(offerId)                              // all editions (for rail)
useOfferWithEdition(offerId, editionId)           // resolved current edition
useEnrollments(offerId, editionId, filters)       // for ventas tab
useOfferAssets(offerId, editionId)                // for assets tab
useOfferCampaigns(offerId, editionId)             // for campañas tab
useOfferCounts(offerId, editionId)                // tab badge counts
useKnowledgeSources(offerId)                      // for info tab section 7
useEditionWaitlist(offerId)                       // for waitlist banner
```

### 6.2 Invalidation
- Mutación en Info → invalidate `["offer", offerId]` + `["edition", editionId]` + `["offer", offerId, "counts"]`.
- Mutación en Ventas → invalidate `["enrollments", ...]` + counts.
- Mutación en Assets → invalidate `["assets", ...]` + counts.
- Mutación en Campañas → invalidate `["campaigns", ...]` + counts.

---

## 7. Test coverage minimums

**Per tab test file:**
- Render happy path with mocked data.
- Render loading state (skeleton).
- Render error state.
- Render empty state.
- Key interactions (filter, switch, CTA).

**Cross-tab test:**
- Switch tab preserves edition.
- Switch edition preserves tab.
- Deep link with tab+edition resolves correctly.

---

## 8. Implementation checklist

**Info:**
- [ ] `OfferInfoTab.tsx` shell
- [ ] `IdentitySection.tsx` + `DatesSection.tsx` + `PricingTiersSection.tsx` + `DeliverablesSection.tsx` + `AudienceSection.tsx` + `GuaranteeOnboardingSection.tsx` + `KnowledgeSection.tsx`
- [ ] `SectionCard.tsx` shared component
- [ ] `CompletenessBadge.tsx` shared component
- [ ] Inline edit mode per section con RHF + Zod
- [ ] Timeline visual con positioning dinámico
- [ ] TierRow component con edit mode
- [ ] FileUpload + KnowledgeStatusBadge

**Ventas:**
- [ ] `OfferVentasTab.tsx` shell
- [ ] `KpiCard.tsx` shared
- [ ] `EnrollmentsTable.tsx` + `EnrollmentRow.tsx`
- [ ] `EnrollmentStatusBadge.tsx`
- [ ] Resend link action
- [ ] Deep link banner

**Assets:**
- [ ] `OfferAssetsTab.tsx` shell
- [ ] `AssetGallery.tsx` + `AssetTile.tsx`
- [ ] Placeholder banner + filter pills
- [ ] Stub page for editor

**Campañas:**
- [ ] `OfferCampanasTab.tsx` shell
- [ ] `CampaignCard.tsx` + `PlatformIcon.tsx` + `PlatformBadge.tsx` + `CampaignStatusBadge.tsx`
- [ ] Associate picker modal
- [ ] Orgánico placeholder

---

## 9. References

- Prototype HTML: `docs/ux-sessions/2026-04-17-offer-editions-ui-revamp/prototype/offer-studio/`
- Backend launch_edition domain: `backend/src/modules/offer/domain/launch_edition.py`
- Backend archetype catalog: `backend/src/modules/offer/domain/archetype_catalog.py`
- Enrollment entity (Phase 5 pending): `UI-SPEC-closer-studio.md` + `FLOW-SPEC-offer-studio-editions.md` § 3.3
