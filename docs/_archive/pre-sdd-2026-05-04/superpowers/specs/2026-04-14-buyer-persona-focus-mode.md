# Buyer Persona — Focus Mode & Co-Creation Experience

**Fecha:** 2026-04-14  
**Estado:** Aprobado  
**Scope:** Brand Studio › Público › Buyer Personas

---

## Contexto

El Brand Studio tiene dos modelos para buyer personas:

| Modelo | Tabla | Estado |
|--------|-------|--------|
| `Avatar` | `avatars` | Legacy — 3 campos simples, en uso actualmente |
| `BuyerPersona` | `buyer_personas` | Nuevo — 12+ campos estructurados, sin API ni UI |

El Interview Engine ya tiene configuración completa para `buyer_persona` (5 bloques, preview registry, ruta de entrevista). Solo faltan el persister de copilot, la API REST, y la UI.

**Decisión:** Migrar completamente de `Avatar` a `BuyerPersona`. Los datos legacy de `avatars` quedan como están (sin migración de datos — la tabla sigue existiendo, solo se deja de usar en la UI).

---

## Tarea 0 — Full-Width Layout (prerequisito global)

**Problema:** El dashboard layout tiene `container mx-auto max-w-7xl` que limita el ancho de todas las páginas. Sales Studio y Offer Studio esquivan esto con `FULL_WIDTH_PATTERNS`, que es un workaround.

**Solución:** Eliminar la restricción de ancho en el wrapper base. Cada sección gestiona su propio `max-w-*` internamente si lo necesita.

**Archivo:** `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx`

```tsx
// Antes
const FULL_WIDTH_PATTERNS = ["/sales/studio", "/offer-studio/offer/"] as const;

function matchesFullWidth(pathname: string): boolean {
  return FULL_WIDTH_PATTERNS.some((pattern) => pathname.includes(pattern));
}

// MemoizedChildren usaba isFullWidth para elegir wrapper

// Después — eliminar FULL_WIDTH_PATTERNS, matchesFullWidth, y el estado isFullWidth
// Siempre usar:
<div className="p-6 md:p-8 h-full">{children}</div>

// Las rutas que eran full-width (sales/studio, offer-studio/offer) usan h-screen internamente
// y no necesitan padding externo — agregar pt-0 donde haga falta.
```

**Efecto:** Páginas con contenido centrado (brand-studio, growth-studio) deben agregar `max-w-5xl mx-auto` o similar en su contenedor interno. Esto se hace progresivamente — no bloquea esta feature.

---

## Journey del usuario

### Estado A — Sin buyer personas

```
PublicoView
└── Empty state inline (sin modal)
    ├── [🧠 Modo Inteligente]  → Tarea 3
    └── [📝 Modo Manual]       → Tarea 5
```

### Estado B — Con personas existentes

```
PublicoView
└── Grid de persona cards
    ├── Card (nombre + avatar initials + completeness bar + [✨ Focus])
    │   ├── Click en card → navega a /brand-studio/publico/persona/[id]
    │   └── Click en ✨ Focus → activa focus mode en copilot sidebar
    └── Card "+ Nueva persona" → vuelve al empty state / elección de modo
```

---

## Tarea 1 — Backend: API REST de BuyerPersona

**Archivo nuevo:** `backend/src/modules/brand/api/buyer_personas.py`

Endpoints con tenant isolation obligatorio en todas las operaciones:

```
GET    /api/v1/brand/buyer-personas/           → list (filtrado por tenant_id)
POST   /api/v1/brand/buyer-personas/           → create
GET    /api/v1/brand/buyer-personas/{id}       → get
PATCH  /api/v1/brand/buyer-personas/{id}       → update parcial (por sección)
DELETE /api/v1/brand/buyer-personas/{id}       → soft delete (is_active=False)
```

**DTOs (`backend/src/modules/brand/api/dto/buyer_personas.py`):**

```python
class BuyerPersonaCreateDTO(BaseModel):
    name: str
    tagline: str | None = None
    scope: str = "GLOBAL"
    offer_id: UUID | None = None

class BuyerPersonaSectionUpdateDTO(BaseModel):
    """PATCH parcial — solo los campos enviados se actualizan."""
    name: str | None = None
    tagline: str | None = None
    demographics: dict | None = None
    psychographics: dict | None = None
    pain_points: list[dict] | None = None
    desires: list[dict] | None = None
    objections: list[dict] | None = None
    preferred_channels: list[dict] | None = None
    buyer_journey: dict | None = None
    purchase_triggers: list[str] | None = None
    anti_patterns: list[str] | None = None

class BuyerPersonaResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    tagline: str | None
    scope: str
    is_primary: bool
    demographics: dict
    psychographics: dict
    pain_points: list[dict]
    desires: list[dict]
    objections: list[dict]
    preferred_channels: list[dict]
    buyer_journey: dict
    purchase_triggers: list[str]
    anti_patterns: list[str]
    completeness_score: float
    interview_session_id: UUID | None
    created_at: datetime
    updated_at: datetime
```

**`completeness_score`:** calculado en el servicio al hacer PATCH — proporción de campos no vacíos sobre total de campos estructurados.

**Registrar router** en `backend/src/modules/brand/api/router.py`.

---

## Tarea 2 — Backend: BuyerPersonaPersister para copilot

El Interview Engine necesita un persister para guardar el `mapa_global` al terminar una entrevista de `buyer_persona`.

**Archivo nuevo:** `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py`

```python
class BuyerPersonaPersister:
    """Guarda el mapa_global de la entrevista en buyer_personas."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def load_existing(self, tenant_id: UUID, entity_id: UUID) -> dict:
        """Carga datos actuales para el snapshot de focus."""
        # SELECT from buyer_personas WHERE id=entity_id AND tenant_id=tenant_id
        ...

    def save(self, tenant_id: UUID, entity_id: UUID | None, mapa_global: dict) -> UUID:
        """Upsert del mapa_global → campos de BuyerPersonaModel."""
        # Mapea mapa_global (dot-notation) → columnas JSONB
        # Si entity_id es None → INSERT nuevo
        # Si entity_id existe → UPDATE
        ...
```

**Registrar** en `persister_registry.py`:
```python
registry = {
    "brand": BrandPersister,
    "offer": OfferPersister,
    "buyer_persona": BuyerPersonaPersister,  # nuevo
}
```

---

## Tarea 3 — Frontend: Empty State con elección de modo

**Archivo:** `frontend/src/features/brand/sections/avatars/avatars-preview.tsx`

Reemplazar el empty state actual por:

```tsx
// Sin personas → inline mode selection
<div className="flex flex-col items-center justify-center py-10 text-center ...">
  <div>Sin Buyer Personas</div>
  <p>¿Cómo quieres crear tu primer buyer persona?</p>

  <div className="flex gap-4">
    {/* Modo Inteligente */}
    <button onClick={handleModoInteligente} className="...border purple...">
      🧠 Modo Inteligente
      <span>Co-crear con copilot</span>
    </button>

    {/* Modo Manual */}
    <button onClick={handleModoManual} className="...border neutral...">
      📝 Modo Manual
      <span>Formulario completo</span>
    </button>
  </div>
</div>
```

**`handleModoInteligente`:**
```tsx
const handleModoInteligente = async () => {
  const token = await getToken();
  // 1. Crear persona shell (solo name por defecto)
  const persona = await buyerPersonaApi.create(token, { name: "Mi buyer persona" });
  // 2. Iniciar entrevista
  const interview = await startInterview(token, "buyer_persona", persona.id);
  // 3. Activar en copilot store
  const store = useCopilotStore.getState();
  store.setFocusEntity({ domain: "buyer_persona", entityId: persona.id, label: persona.name });
  store.setInterviewSession(interview.session_id);
  store.setConversationId(interview.conversation_id);
  store.addMessage({ role: "assistant", content: interview.initial_message, ... });
  store.setSidebarState("expanded");
};
```

**`handleModoManual`:**
```tsx
const handleModoManual = async () => {
  const token = await getToken();
  const persona = await buyerPersonaApi.create(token, { name: "Mi buyer persona" });
  router.push(`/${tenantId}/brand-studio/publico/persona/${persona.id}`);
};
```

**Primer mensaje del copilot para `buyer_persona`:**  
Actualizar `interview_service.py` — agregar campo `initial_message` a `InterviewConfig` o manejar por dominio:

```python
INITIAL_MESSAGES = {
    "buyer_persona": (
        "Un buyer persona es el perfil de tu cliente ideal: quién es, qué le duele, qué desea. "
        "Vamos a construirlo juntos con preguntas simples.\n\n"
        "Para empezar — ¿cómo quieres llamarle a este segmento de clientes?"
    ),
    "brand": "¡Hola! Vamos a construir tu marca juntos. Cuéntame, ¿cómo nació tu negocio?",
    "offer": "¡Hola! Vamos a construir tu oferta juntos. ...",
}
```

---

## Tarea 4 — Frontend: Persona Cards con chip Focus

**Archivo:** `frontend/src/features/brand/sections/avatars/avatars-preview.tsx`

Migrar el fetch de `avatarApi.listAvatars` → `buyerPersonaApi.list`.

Cada card:
```tsx
<div key={persona.id} className="...">
  {/* Avatar initials */}
  <Avatar>
    <AvatarFallback>{persona.name.substring(0, 2).toUpperCase()}</AvatarFallback>
  </Avatar>

  {/* Name + completeness */}
  <h4>{persona.name}</h4>
  <Progress value={persona.completeness_score * 100} />

  {/* Focus chip — siempre visible */}
  <FocusModeButton
    domain="buyer_persona"
    entityId={persona.id}
    label={persona.name}
    entityData={persona as unknown as Record<string, unknown>}
    className="mt-2 w-full rounded-full text-xs"
  />
</div>
```

Click en la card navega a `/brand-studio/publico/persona/[id]`.  
Click en el chip activa focus mode (FocusModeButton ya hace `setFocusEntity` + `setSidebarState("expanded")`).

---

## Tarea 5 — Frontend: Persona Detail Page (Modo Manual)

**Ruta nueva:** `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/publico/persona/[personaId]/page.tsx`

Con Tarea 0 completada, esta ruta ya es full-width automáticamente (no necesita `FULL_WIDTH_PATTERNS`).

**Layout:**
```
┌─ Topbar ─────────────────────────────────────────────────────┐
│ ‹ Buyer Personas / [nombre]                    Guardado ●    │
├─ Nav (220px) ──┬─ Form area (flex-1) ──────────────────────┤
│ [persona info] │ [section header]                           │
│                │                                            │
│ • Demografía ✓ │ [2-col field grid]                        │
│ • Dolores ●    │ [WithCopilot en cada campo]               │
│ • Psicografía  │                                            │
│ • Objeciones   │                                [Guardar]  │
│ • Canales      │                                           │
│                │                                           │
│ ─────────────  │                                           │
│ Progress: 45%  │                                           │
└────────────────┴───────────────────────────────────────────┘
```

**Secciones del nav (mapean a bloques del interview config):**

| ID | Label | Campos principales |
|----|-------|-------------------|
| `demographics` | Demografía | age_range, location, occupation, income_range, education |
| `pain_desire` | Dolores & Deseos | pain_points[], desires[], impacto emocional |
| `psychographics` | Psicografía | values[], beliefs[], lifestyle, media_consumption |
| `objections` | Objeciones | objections[], purchase_triggers[], anti_patterns[] |
| `channels_journey` | Canales & Journey | preferred_channels[], buyer_journey{} |

**Comportamiento:**
- Cada sección guarda con PATCH parcial al endpoint `/api/v1/brand/buyer-personas/{id}`
- Auto-save: debounce de 1.5s al cambiar campos
- `completeness_score` se recalcula en el backend al hacer PATCH y se refleja en el nav
- `WithCopilot` wrapper en cada campo — funciona igual que en offer/brand

**Hook:** `useBuyerPersona(personaId)` — fetch + optimistic PATCH.

---

## Tarea 6 — Frontend: Hook y cliente API

**Archivo nuevo:** `frontend/src/lib/api/buyer-persona.ts`

```ts
export const buyerPersonaApi = {
  list: (token: string) => fetchClient("/api/v1/brand/buyer-personas/", { token }),
  get: (token: string, id: string) => fetchClient(`/api/v1/brand/buyer-personas/${id}`, { token }),
  create: (token: string, data: BuyerPersonaCreateDTO) =>
    fetchClient("/api/v1/brand/buyer-personas/", { token, method: "POST", body: data }),
  patch: (token: string, id: string, data: Partial<BuyerPersonaSectionUpdateDTO>) =>
    fetchClient(`/api/v1/brand/buyer-personas/${id}`, { token, method: "PATCH", body: data }),
  delete: (token: string, id: string) =>
    fetchClient(`/api/v1/brand/buyer-personas/${id}`, { token, method: "DELETE" }),
};
```

**Hook:** `frontend/src/features/brand/hooks/useBuyerPersonas.ts` — React Query con `queryKey: ["buyer_personas"]`.

---

## Fuera de scope (esta iteración)

- Migración de datos de `avatars` → `buyer_personas` (datos existentes quedan en Avatar)
- Eliminar la API de `avatars` (deprecación progresiva)
- Buyer persona por oferta (`scope: "OFFER"`) — solo `GLOBAL` por ahora
- Headshot / imagen del avatar
- Compartir buyer persona entre tenants

---

## Tests requeridos (TDD — tests antes de implementación)

| Capa | Test |
|------|------|
| Backend API | `test_buyer_persona_api.py` — CRUD + tenant isolation + 404 ajeno |
| Backend persister | `test_buyer_persona_persister.py` — save mapea mapa_global correctamente |
| Architecture | `test_extraction_contract.py` — no aplica; `test_no_cross_module_imports.py` — buyer_persona persister no importa de brand directamente |
| Frontend hook | `useBuyerPersonas.test.ts` — list, create, patch |
| Frontend card | `avatars-preview.test.tsx` — chip Focus visible, click navega |
| Frontend empty state | click Modo Inteligente llama `startInterview`, click Modo Manual navega |

---

## Orden de implementación

```
Task 0  → full-width layout (1 archivo, ~10 líneas)
Task 1  → backend API + DTOs
Task 2  → BuyerPersonaPersister + registro
Task 6  → frontend API client + hook
Task 3  → empty state con modo selection
Task 4  → persona cards con chip Focus
Task 5  → persona detail page (full-width)
```

Tasks 1+2 son independientes entre sí y pueden ir en paralelo.  
Tasks 3+4+5 dependen de Task 6 (necesitan el API client).
