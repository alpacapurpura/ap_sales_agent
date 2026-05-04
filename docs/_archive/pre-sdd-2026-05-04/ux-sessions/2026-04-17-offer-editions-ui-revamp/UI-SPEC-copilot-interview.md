# UI-SPEC — Copilot Interview Date Block

> **Scope:** Nuevo bloque final del interview de creación de oferta: pregunta obligatoria "¿Cuándo tu primera edición?" con split view (chat + preview en vivo).
>
> **Reference prototype:** `prototype/copilot/interview-date.html`.

---

## 1. Integration

### 1.1 Backend config extension

Editar `backend/src/modules/copilot/domain/interview_configs/offer_config.py` para agregar al final (tras todos los bloques existentes de extracción):

```python
BLOCKS.append(
    InterviewBlock(
        id="first_edition_date",
        question_template_es="¿Cuándo planeas tu primera {edition_noun_es}?",
        question_fallback_es="¿Cuándo planeas lanzar esta oferta por primera vez?",
        required=True,
        # condicional: sólo si el archetype extraído en bloque previo soporta ediciones
        skippable=True,
        skippable_warning_es=(
            "Sin fecha, la edición queda privada y los leads van a waitlist. "
            "Podés configurar la fecha después desde la edición."
        ),
        extraction_schema=FirstEditionInput,  # Pydantic schema
        quick_replies_generator=generate_date_quick_replies,
        condition=lambda ctx: get_capabilities(ctx.offer.archetype).supports_editions,
    )
)
```

### 1.2 Quick replies generator

```python
def generate_date_quick_replies(ctx: InterviewContext) -> list[QuickReply]:
    suggested = suggest_first_edition_date(ctx)
    capabilities = get_capabilities(ctx.offer.archetype)
    noun = capabilities.edition_noun_es or "edición"
    
    return [
        QuickReply(
            type="date_suggestion",
            label_es=f"📅 El {format_date_es(suggested)}",
            value=suggested.isoformat(),
            auto_generated=True,
        ),
        QuickReply(
            type="date_picker",
            label_es="📅 Elegir fecha…",
            value=None,  # abre el date picker
        ),
        QuickReply(
            type="skip",
            label_es="🤷 Todavía no sé",
            value=None,
        ),
    ]
```

**`suggest_first_edition_date(ctx)` heuristics:**
- Si en bloques previos el usuario mencionó un mes/fecha → parsear y sugerir el lunes más cercano.
- Else: +6 semanas desde hoy, ajustar al siguiente lunes 19:00 hora tenant.

### 1.3 Procedure update

Editar `backend/src/modules/copilot/application/procedures/offer_creation.py`:

```python
async def execute(self, ctx: InterviewContext) -> OfferCreationResult:
    # ... existing logic creates offer
    offer = await self._create_offer(ctx)  # emits OfferCreated, placeholder edition created
    
    # NEW: process first_edition_date block
    first_edition_input = ctx.get_block_answer("first_edition_date")
    if first_edition_input and first_edition_input.start_date:
        placeholder_edition = await self.edition_repo.get_placeholder(offer.id, tenant_id)
        await self.edition_service.update_and_publish(
            edition_id=placeholder_edition.id,
            start_date=first_edition_input.start_date,
            end_date=first_edition_input.end_date,
            location_override=first_edition_input.location_override,
            tenant_id=tenant_id,
        )
        # edition transitions to UPCOMING + PUBLIC
    
    # redirect target
    target_edition_id = placeholder_edition.id if first_edition_input else None
    redirect_url = f"/offer-studio/offer/{offer.id}"
    if target_edition_id:
        redirect_url += f"?edition={target_edition_id}"
    
    return OfferCreationResult(offer=offer, redirect_url=redirect_url)
```

---

## 2. Frontend component

**File:** `frontend/src/features/copilot/components/interview/InterviewDateBlock.tsx`

### 2.1 Integration

El interview frontend ya tiene un pattern para renderizar bloques conversacionales. Agregar nuevo block handler:

```tsx
// frontend/src/features/copilot/components/interview/BlockRenderer.tsx
export function BlockRenderer({ block }: { block: InterviewBlock }) {
  switch (block.type) {
    case "text_capture": return <TextCaptureBlock ... />;
    case "single_choice": return <SingleChoiceBlock ... />;
    case "file_upload": return <FileUploadBlock ... />;
    case "first_edition_date": return <InterviewDateBlock block={block} />;  // NEW
    // ...
  }
}
```

### 2.2 Component structure

Layout: split view con chat a la izquierda (60%) + preview en vivo a la derecha (40%).

```tsx
<section className="grid grid-cols-5 h-[calc(100vh-160px)]">
  {/* Chat pane */}
  <div className="col-span-3 bg-white border-r border-slate-200 flex flex-col">
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      <AssistantMessage>
        Listo, ya tengo tu oferta: <strong>{offerName}</strong> ({archetypeLabel}, nivel {valueLevel}).
        Antes de terminar, algo clave:
      </AssistantMessage>
      
      <AssistantMessage prominent>
        <p className="font-semibold mb-1">{block.question}</p>
        <p className="text-xs text-slate-600">
          Esto me permite publicar la edición y que el agente de ventas pueda ofrecerla a leads.
        </p>
      </AssistantMessage>
      
      {/* Quick replies */}
      <div className="flex gap-2 flex-wrap ml-11">
        {block.quick_replies.map(qr => (
          <QuickReplyButton
            key={qr.type}
            variant={qr.auto_generated ? 'prominent' : 'normal'}
            onClick={() => handleReply(qr)}
          >
            {qr.label_es}
          </QuickReplyButton>
        ))}
      </div>
      
      {/* Hint */}
      <div className="ml-11 text-xs text-slate-500 italic">
        💡 Si no sabés, creo la edición en borrador y la publicás cuando tengas la fecha.
        Mientras tanto el agente pondrá leads en <strong>lista de espera</strong>.
      </div>
    </div>
    
    <InterviewInput placeholder="O escribí tu respuesta…" onSend={handleFreeText} />
  </div>
  
  {/* Preview pane */}
  <aside className="col-span-2 bg-slate-50 p-6 overflow-y-auto">
    <p className="text-xs font-semibold text-slate-500 uppercase mb-3">Vista en vivo</p>
    <OfferPreviewCard offer={ctx.offer} />
    
    <p className="text-xs font-semibold text-slate-500 uppercase mb-2 mt-4">
      {capabilityLabels.edition_noun_plural.capitalize()} #1
      {!selectedDate && <span className="ml-1 text-[10px] text-purple-600 normal-case">pendiente de fecha</span>}
    </p>
    
    <EditionPreviewCard
      startDate={selectedDate}
      visibility={selectedDate ? 'public' : 'private'}
      status={selectedDate ? 'upcoming' : 'draft'}
      capacity={ctx.offer.suggested_capacity || 50}
    />
    
    <div className="text-xs text-slate-500 mt-4 flex items-center gap-2">
      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
      5 pasos completados · {selectedDate ? '¡terminá!' : 'solo falta la fecha'}
    </div>
  </aside>
</section>
```

### 2.3 Quick reply buttons

```tsx
interface QuickReplyButtonProps {
  variant: 'prominent' | 'normal';
  children: React.ReactNode;
  onClick: () => void;
}

<button
  className={cn(
    "px-4 py-2 bg-white border rounded-lg text-sm transition",
    variant === 'prominent'
      ? "border-2 border-purple-300 hover:border-purple-500 font-medium"
      : "border-slate-200 hover:border-slate-400"
  )}
  onClick={onClick}
>
  {children}
</button>
```

### 2.4 Handle reply

```tsx
async function handleReply(qr: QuickReply) {
  if (qr.type === 'date_suggestion') {
    await submitAnswer({ start_date: qr.value });
  } else if (qr.type === 'date_picker') {
    setDatePickerOpen(true);
  } else if (qr.type === 'skip') {
    // show confirm
    const confirmed = await confirmDialog({
      title: '¿Crear edición sin fecha?',
      description: 'La edición quedará en borrador y privada. Los leads van a waitlist.',
      confirmLabel: 'Sí, crear en borrador',
    });
    if (confirmed) {
      await submitAnswer({ start_date: null });
    }
  }
}

async function handleDatePickerConfirm(date: Date) {
  setDatePickerOpen(false);
  setSelectedDate(date);  // update preview immediately
  await submitAnswer({ start_date: date.toISOString() });
}
```

### 2.5 EditionPreviewCard

```tsx
interface EditionPreviewCardProps {
  startDate: string | null;
  visibility: 'private' | 'public';
  status: 'draft' | 'upcoming';
  capacity: number;
}

<div className={cn(
  "bg-white rounded-xl p-4 mb-4",
  status === 'draft' ? "border-2 border-dashed border-amber-300" : "border border-blue-200 ring-1 ring-blue-100"
)}>
  <div className="flex items-center justify-between mb-3">
    <span className="font-semibold text-sm">{capabilityLabels.edition_noun_singular.capitalize()} #1 · {formatMonth(startDate || nextMonth)}</span>
    <StatusBadge status={status} />
  </div>
  <div className="space-y-2 text-xs text-slate-600">
    <Row label="Inicio">
      {startDate
        ? formatFullDate(startDate)
        : <span className="text-amber-600 font-medium">{format(suggested)} (pendiente de confirmar)</span>
      }
    </Row>
    <Row label="Capacidad">{capacity} estudiantes</Row>
    <Row label="Visibilidad"><VisibilityBadge visibility={visibility} /></Row>
  </div>
  <p className="mt-3 text-[11px] text-slate-500 border-t border-slate-100 pt-2">
    Cuando confirmes, pasará a <strong>Próxima + Pública</strong> y el agente podrá venderla.
  </p>
</div>
```

### 2.6 Progress indicator in header

El header del interview (existente) ya tiene un progress bar. Para este último bloque:

```tsx
<header>
  <BackButton href="/offer-studio" />
  <div>
    <h1>Crear oferta con IA — Interview</h1>
    <p className="text-xs text-slate-500">
      Paso {currentStep} de {totalSteps} · Programando tu primera {edition_noun_es}
    </p>
  </div>
  <Progress value={(currentStep / totalSteps) * 100} />
  <span>{Math.round((currentStep / totalSteps) * 100)}%</span>
</header>
```

---

## 3. Behaviors

### 3.1 Auto-advance after answer

Tras click en quick reply o confirmación del date picker:
1. Inline submit: POST `/api/v1/copilot/interviews/{interview_id}/answers` con `{block_id: 'first_edition_date', value: {...}}`.
2. Backend procesa y finaliza el interview.
3. Response incluye `redirect_url`.
4. Client navega a `redirect_url` (ej. `/offer-studio/offer/abc?edition=xyz`).
5. Success toast: "¡Oferta creada! Edición #1 publicada para el {fecha}" o "¡Oferta creada! Edición #1 en borrador."

### 3.2 Skip warning modal

Cuando usuario elige "Todavía no sé":
- Abrir modal de confirmación.
- Modal mesaje: "Sin fecha, la edición queda privada. Los leads van a waitlist hasta que configures una fecha. ¿Confirmás?"
- Buttons: `[Cancelar]` · `[Sí, crear en borrador]`.

### 3.3 Date picker

Component `<DatePicker />` ya existe en `frontend/src/components/ui/date-picker.tsx` (asumiendo Shadcn). Open en modal.

Config:
- `minDate`: hoy + 1 día.
- Default value: suggested date del quick-reply.
- Locale: `es`.
- Formato: "lun 15 jul 2026".

### 3.4 Free text input

Si usuario escribe en vez de usar quick-reply (ej. "en agosto"):
- Backend parsea NL con `date-parser` (extiste una lib o usar Sonnet fine-tune).
- Si parseable → confirmar: "Entendí '15 de agosto de 2026'. ¿Correcto?".
- Si no parseable → "No pude entender la fecha. ¿Podrías elegir de los botones de arriba?".

---

## 4. Copy details

### 4.1 Archetype-specific question

Usar `edition_noun_es` del catálogo:
- PROGRAMA: "¿Cuándo planeas tu primera cohorte?"
- EXPERIENCIA: "¿Cuándo planeas tu primera salida?"
- SERVICIO: "¿Cuándo planeas tu primera convocatoria?"
- Fallback (sin noun): "¿Cuándo planeas lanzar esta oferta por primera vez?"

### 4.2 Skip confirmation

```
Título: ¿Crear {edition_noun_es} sin fecha?
Body: La {edition_noun_es} quedará en borrador y privada. Los leads van a waitlist hasta que configures una fecha.

[Cancelar] [Sí, crear en borrador]
```

### 4.3 Success toast

- Con fecha: "¡Oferta creada! {capitalize(edition_noun_es)} #1 publicada para el {formatDate}"
- Sin fecha: "¡Oferta creada! {capitalize(edition_noun_es)} #1 en borrador. Cuando definas fecha, publicala."

---

## 5. Test scenarios

### 5.1 Vitest
- `InterviewDateBlock.test.tsx`:
  - Renders question + 3 quick replies.
  - Click `date_suggestion` → submit with ISO date.
  - Click `date_picker` → modal opens.
  - Click `skip` → confirm dialog opens; confirm → submit null.
  - Preview card updates con fecha seleccionada.

- `OfferCreationProcedure.test.py` (backend):
  - `test_creation_with_first_edition_date_publishes_edition`
  - `test_creation_skip_keeps_placeholder_draft`
  - `test_creation_non_editioned_archetype_skips_block`

### 5.2 E2E
`frontend/e2e/specs/regression/copilot-interview-date.spec.ts`:
- Crear oferta PROGRAMA via interview.
- Avanzar hasta el último bloque.
- Verificar pregunta "¿Cuándo planeas tu primera cohorte?".
- Click en date suggestion.
- Redirect a offer con `?edition={id}` en URL.
- Rail muestra Edición #1 como Próxima con la fecha.

---

## 6. Implementation checklist

**Backend:**
- [ ] Extender `offer_config.py` con `first_edition_date` block
- [ ] Implementar `generate_date_quick_replies` + `suggest_first_edition_date`
- [ ] Actualizar `OfferCreationProcedure.execute` para manejar `first_edition` input
- [ ] Agregar `LaunchEditionService.update_and_publish(edition_id, start_date, ...)` si no existe
- [ ] Tests unitarios

**Frontend:**
- [ ] `InterviewDateBlock.tsx` con split view
- [ ] `EditionPreviewCard.tsx` con estados draft/upcoming
- [ ] `QuickReplyButton.tsx` shared component
- [ ] Integración en `BlockRenderer.tsx`
- [ ] Date picker modal + free text parsing
- [ ] Skip confirm dialog
- [ ] Success toast logic
- [ ] Vitest tests
- [ ] E2E regression test

---

## 7. References

- Prototype HTML: `prototype/copilot/interview-date.html`
- Archetype catalog: `backend/src/modules/offer/domain/archetype_catalog.py`
- Existing interview framework: `frontend/src/features/copilot/components/interview/`
- Existing copilot procedures: `backend/src/modules/copilot/application/procedures/`
