# FLOW-SPEC — Brand Studio: Sección "Estilo Comunicacional"

**Scope:** Studio-scoped (Brand Studio).
**Date:** 2026-04-21.
**Owner:** UX Flow Architect (Chris).
**Status:** Diseño aprobado, pendiente implementación.

---

## 1. Summary

- Extraer la voz/estilo de conversación de `identity` a una **sección propia top-level** en Brand Studio.
- Slug propuesto: `estilo` (consistente con `publico`). Etiqueta UI: **Estilo Comunicacional**.
- Eliminar los 2 campos de identity: `voice_tone` (textarea libre) y `voice_tone_clone` (placeholder custom).
- La sección expone lo que el backend **ya tiene implementado**: 6 presets (`PERSONALITY_PRESETS`), DimensionContract (6 dimensiones × 5 niveles), PersonalityCompiler (5 bloques → `system_instruction`), simulación, CRUD de `PersonalityProfile`.
- **Falta en backend:** `POST /personality/clone` hoy retorna 501 — la clonación conversacional debe cablearse al LangGraph `personality_app` ya existente (`backend/src/modules/brand/application/agents/style_analyzer/graph.py`).
- **Impacto downstream:** `sales_agent` y generadores de copy (landing, email, assets) migran de leer `BrandIdentity.voice_tone` (string) a leer `PersonalityProfile.system_instruction` (activo por tenant, vía `GET /personality/active`).

---

## 2. Current Navigation Map (contexto)

Brand Studio tiene 13 secciones en `BRAND_SECTIONS` (`frontend/src/features/brand-studio/lib/section-catalog.ts:34-48`):

```
publico · identity · positioning · narrative · methodology · story ·
team · authority · testimonials · visuals · communication-assets · contact · legal
```

La voz vive hoy **dentro de `identity`** como 2 fields del schema (`identity.schema.ts:42-70`):

- `voice_tone` — textarea libre, consumido por SDR, landing y captions.
- `voice_tone_clone` — field `type: custom`, `action: voice-clone`, hoy renderiza `VoiceClonePlaceholder` ("pendiente Sprint 2"). El comentario en `section-page-map.ts:28` confirma: _"voice → subset of identity; renders under identity page"_.

El archivo `frontend/src/features/brand-studio/schemas/voice.schema.ts` duplica ambos campos y está huérfano (no se referencia desde `SECTION_PAGE_MAP`). Candidato a borrar tras migración.

Backend tiene todo el pipeline:

| Capa | Archivo | Rol |
|---|---|---|
| API | `backend/src/modules/brand/api/personality.py` | 7 endpoints REST (`/presets`, `/active`, `/select-preset`, `/clone` [501], `/{id}/dimensions`, `/{id}/simulate`, `DELETE /{id}`) |
| Domain | `backend/src/modules/brand/domain/personality.py` | 6 presets + DimensionContract + PersonalityCompiler + PersonalityProfile entity |
| Service | `backend/src/modules/brand/application/services/personality_service.py` | select_preset, update_dimensions, delete_with_anchors |
| Graph | `backend/src/modules/brand/application/agents/style_analyzer/graph.py` | `personality_app`: parser→janitor→psychologist→architect→embedder→simulator |
| Qdrant | `backend/src/modules/brand/infrastructure/qdrant/style_anchor_store.py` | Collection `personality_style_anchors` |
| Storage | `backend/src/modules/brand/infrastructure/models/personality_model.py` | `personality_profiles` table (JSONB columns) |

---

## 3. Proposed Navigation

### Sidebar (nav rail brand-studio)

**Antes → Después:** inserta `estilo` en posición 3, justo después de `identity`.

```
Antes                         Después
1. publico                    1. publico
2. identity                   2. identity                  ← drop voice_tone + voice_tone_clone
                              3. estilo [NEW]               ← Estilo Comunicacional
3. positioning                4. positioning
4. narrative                  5. narrative
5. methodology                6. methodology
6. story                      7. story
7. team                       8. team
8. authority                  9. authority
9. testimonials               10. testimonials
10. visuals                   11. visuals
11. communication-assets      12. communication-assets
12. contact                   13. contact
13. legal                     14. legal
```

**Justificación del orden:** identity es el anclaje narrativo; `estilo` es la expresión superficial de esa identidad. Después viene positioning (qué promete), narrative (la historia). Orden: **quién eres → cómo hablas → qué prometes → cómo lo cuentas**.

**Icono:** `MessageCircle` o `Mic` de lucide-react (nav rail usa lucide). Propuesta: `MessageCircle`.

### Ruta Next.js

- Dashboard: `/[tenantId]/brand-studio/estilo`
- Sub-rutas opcionales (drill-ins en el mismo page con state local, no Next routes nuevas):
  - Preset picker como modal/drawer → no necesita ruta.
  - Clone wizard como drawer de 3 pasos → no necesita ruta.
  - "Probar en conversación" como drawer → no necesita ruta.

Razón: la sección vive en una sola página (estado vacío / estado activo) con overlays. Simplifica routing y preserva Server Component patrón estándar de brand-studio.

---

## 4. Screens (ASCII Wireframes)

### 4.1 Empty state — sin perfil activo

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Brand Studio / Estilo Comunicacional                          │
│                                                                  │
│ Estilo Comunicacional                            [?] Ayuda  •••  │
│ Cómo habla tu marca en cada conversación. El SDR y las           │
│ piezas auto-generadas (landing, email, captions) usan este       │
│ estilo.                                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Todavía no tienes un estilo activo.                            │
│   Elige cómo empezar:                                            │
│                                                                  │
│   ┌─────────────────────────────┐  ┌─────────────────────────┐  │
│   │ ☀️ Empezar con un preset     │  │ 🧬 Clonar mi estilo      │  │
│   │                             │  │                         │  │
│   │ 6 estilos base listos para  │  │ Pega mensajes tuyos     │  │
│   │ usar. Ajustable después.    │  │ reales y genero uno      │  │
│   │                             │  │ único. 2-4 min.          │  │
│   │ ⏱ 30 seg                    │  │                         │  │
│   │                             │  │                         │  │
│   │ [ Ver los 6 presets → ]      │  │ [ Empezar a clonar → ]  │  │
│   └─────────────────────────────┘  └─────────────────────────┘  │
│                                                                  │
│   Sugerencia: empieza con un preset, clona después. El preset    │
│   queda como respaldo por si la clonación no te convence.        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Active state — perfil seleccionado

```
┌─────────────────────────────────────────────────────────────────┐
│ Estilo Comunicacional                   [Cambiar estilo ▾]       │
│ Activo: ☀️ Cálida y Cercana · preset · Actualizado hace 2 días    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Dimensiones                                      [Editar]        │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Energía        Calma   ●─●─○─○─○   Eléctrica   0.35    │     │
│  │ Calidez        Distante ○─○─○─●─●  Íntima      0.85    │     │
│  │ Humor          Serio   ○─●─●─○─○   Cómico      0.6     │     │
│  │ Expresividad   Min     ○─○─●─●─○   Max         0.7     │     │
│  │ Narrativa      Factual ○─○─●─○─○   Cine        0.5     │     │
│  │ Verbosidad     Tele    ○─●─○─○─○   Elaborado   0.4     │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Huella lingüística                              [Editar]         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Saludo:     ¡Hola! ¿Cómo estás?                        │     │
│  │ Despedida:  ¡Un abrazo!                                │     │
│  │ Emojis:     😊 🔥 💪 💛 🤗                                │     │
│  │ Muletillas: "mira" · "te cuento" · "la verdad es que"  │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Ejemplos de conversación                       [Regenerar]      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Contexto: saludo                                       │     │
│  │ Lead → Hola, buenas tardes                             │     │
│  │ Tú   → ¡Hola! ¿Cómo estás? 😊 Qué bueno que me         │     │
│  │        escribes. Cuéntame, ¿en qué te puedo ayudar?    │     │
│  ├────────────────────────────────────────────────────────┤     │
│  │ Contexto: objeción de precio                           │     │
│  │ Lead → Es muy caro, no sé si puedo                     │     │
│  │ Tú   → Te entiendo perfecto, la verdad es que yo       │     │
│  │        también pensé lo mismo cuando empecé 😊 ¿Te     │     │
│  │        cuento lo que le pasó a Laura...                │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  [ Probar en conversación → ]   [ Ver instrucción compilada ]    │
│                                                                  │
│  Downstream: este estilo se usa en                                │
│  · SDR (sales_agent) · Copy de landings · Captions de assets     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Preset picker (drawer lateral o página secundaria con back)

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Volver a Estilo                                                │
│ Elige un preset                                                  │
│ 6 estilos base. Cada uno es un punto de partida — podrás         │
│ ajustar dimensiones y ejemplos después.                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────┐  ┌─────────────────────────┐       │
│  │ ☀️ Cálida y Cercana      │  │ ⚡ Eléctrica y Expresiva │       │
│  │                         │  │                         │       │
│  │ Cercana como una amiga. │  │ Energía desbordante.    │       │
│  │ Valida emociones, humor │  │ MAYÚSCULAS, emojis en   │       │
│  │ ligero, calidez real.   │  │ cascada, ritmo ágil.    │       │
│  │                         │  │                         │       │
│  │ Ejemplo:                │  │ Ejemplo:                │       │
│  │ "¡Hola! ¿Cómo estás? 😊 │  │ "¡¡HOLAAA!! 🔥🔥 ¡Aquí, │       │
│  │ Qué bueno que me..."    │  │ con toda la energía..." │       │
│  │                         │  │                         │       │
│  │ Para: mentoras, coaches │  │ Para: fitness, high     │       │
│  │ bienestar, infoprod.    │  │ voltage, emprendimiento │       │
│  │                         │  │                         │       │
│  │ [ Previa ] [ Activar ]  │  │ [ Previa ] [ Activar ]  │       │
│  └─────────────────────────┘  └─────────────────────────┘       │
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐       │
│  │ 🧠 Serena y Articulada  │  │ 🔥 Directa y Sin Filtro  │       │
│  │                         │  │                         │       │
│  │ Calma con autoridad.    │  │ Dice lo que piensa.     │       │
│  │ Humor seco, sin ruido   │  │ Corto, contundente,     │       │
│  │ visual.                 │  │ confronta objeciones.   │       │
│  │                         │  │                         │       │
│  │ Para: consultoría,      │  │ Para: B2B, high ticket, │       │
│  │ premium, sofisticadas.  │  │ audiencias masculinas.  │       │
│  │                         │  │                         │       │
│  │ [ Previa ] [ Activar ]  │  │ [ Previa ] [ Activar ]  │       │
│  └─────────────────────────┘  └─────────────────────────┘       │
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐       │
│  │ 📖 Narrativa y Vívida   │  │ 🖤 Minimalista y Premium │       │
│  │                         │  │                         │       │
│  │ Todo es historia.       │  │ Menos es más. Cero      │       │
│  │ Metáforas, loops,       │  │ emojis. Cada palabra    │       │
│  │ detalles sensoriales.   │  │ pesa. Exclusividad.     │       │
│  │                         │  │                         │       │
│  │ Para: coaches, marca    │  │ Para: lujo, high ticket, │       │
│  │ personal, storytellers. │  │ acceso restringido.     │       │
│  │                         │  │                         │       │
│  │ [ Previa ] [ Activar ]  │  │ [ Previa ] [ Activar ]  │       │
│  └─────────────────────────┘  └─────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

**Previa** (modal sobre la card): muestra las 6 `SampleExchange` completas + dimensiones en sliders read-only. Botón `Activar este estilo`.

### 4.4 Clone wizard (3 pasos, drawer o página secundaria)

**Paso 1 — Material:**

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Volver a Estilo                                                │
│ Clonar tu estilo                                                 │
│ ● Material   ○ Análisis   ○ Previa                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ¿Cómo quieres aportar tu material?                              │
│                                                                  │
│  ◉ Pegar texto       ○ Subir archivo                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Pega 10 o más mensajes tuyos reales. Variedad importa:  │     │
│  │ saludos, objeciones, cierres, follow-ups.              │     │
│  │                                                         │     │
│  │ Yo: Hola Marce! me encantó tu post 💛...               │     │
│  │ Yo: Mira te cuento, el programa tiene 3 opciones...    │     │
│  │ Yo: Te entiendo perfecto, yo pasé por lo mismo...      │     │
│  │ ...                                                     │     │
│  └────────────────────────────────────────────────────────┘     │
│  Detectado: 127 mensajes · formato chat plano                    │
│                                                                  │
│  Consejo: cuantos más contextos (saludo, precio, objeción,       │
│  cierre), más fiel el clon. Mínimo 10, óptimo 50+.               │
│                                                                  │
│  [ Cancelar ]                        [ Analizar mi estilo → ]    │
└─────────────────────────────────────────────────────────────────┘
```

**Paso 2 — Análisis (streaming state):**

```
┌─────────────────────────────────────────────────────────────────┐
│ ● Material   ● Análisis   ○ Previa                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Analizando tu estilo...                                         │
│                                                                  │
│  ✓ Parseo de mensajes           127 mensajes                     │
│  ✓ Limpieza de ruido             98 mensajes útiles              │
│  ⋯ Perfil psicológico           (≈ 40 seg)                       │
│  · Arquitectura del estilo                                       │
│  · Huella lingüística                                            │
│  · Simulación                                                    │
│                                                                  │
│  Esto suele tardar 2-4 minutos. Puedes cerrar esta ventana;      │
│  te avisamos cuando termine. El estilo anterior sigue activo     │
│  hasta que actives el nuevo.                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Paso 3 — Previa + activación:**

```
┌─────────────────────────────────────────────────────────────────┐
│ ● Material   ● Análisis   ● Previa                               │
├─────────────────────────────────────────────────────────────────┤
│  Así habla tu estilo clonado                                     │
│                                                                  │
│  Dimensiones detectadas:                                         │
│  Energía 0.72  Calidez 0.84  Humor 0.45                          │
│  Expresividad 0.68  Narrativa 0.6  Verbosidad 0.4                │
│  [ Ajustar dimensiones ]                                         │
│                                                                  │
│  Huella lingüística detectada:                                   │
│  Saludo:     "Hola preciosa!"                                    │
│  Despedida:  "abrazos"                                           │
│  Emojis favoritos: 💛 🌿 ✨                                       │
│  Muletillas: "la verdad", "mira", "te cuento"                    │
│                                                                  │
│  Ejemplos generados con tu estilo:                               │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Contexto: objeción de precio                           │     │
│  │ Lead → Está caro para mí                               │     │
│  │ Tú   → Mira, te entiendo 💛 ¿te cuento cómo lo hizo Lu │     │
│  │        que estaba igual? la verdad es que...           │     │
│  └────────────────────────────────────────────────────────┘     │
│  [ Regenerar ejemplos ]                                          │
│                                                                  │
│  [ ← Descartar ]                [ Activar este estilo → ]         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 Probar en conversación (drawer)

```
┌─────────────────────────────────────────────────────────────────┐
│ Probar en conversación                               [ × ]       │
│ Estilo activo: ☀️ Cálida y Cercana                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Mensaje del lead (simulado):                                    │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Hola, cuánto cuesta tu programa?                       │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  [ Saludo ] [ Precio ] [ Objeción ] [ Interés ] [ Cierre ]       │
│                                                                  │
│  [ Generar respuesta → ]                                         │
│                                                                  │
│  Respuesta del SDR con este estilo:                              │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ ¡Hola! Mira, te cuento 😊 Tiene 3 opciones para que     │     │
│  │ elijas la que mejor te quede. ¿Te las muestro?         │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  [ Otra simulación ]                     [ Volver al estilo ]    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow End-to-End

### 5.1 Lectura (page load)

```
Server Component /brand-studio/estilo
  └─▶ fetch(`${api}/api/v1/brand/personality/active`, { cache: "no-store" })
      ├─▶ null         → renderiza EmptyState
      └─▶ ProfileDTO   → renderiza ActiveState con sliders + ejemplos
```

### 5.2 Flujo preset

```
User click "Activar" en Cálida y Cercana
  └─▶ POST /api/v1/brand/personality/select-preset  { preset_key: "warm_close" }
      └─▶ PersonalityService.select_preset(tenant_id, preset_key)
          ├─▶ deactivate_active_global(tenant_id)
          ├─▶ PersonalityProfileModel row: profile_type="preset", preset_key="warm_close",
          │   dimensions/linguistic_patterns/sample_exchanges copiados del PresetDefinition
          ├─▶ PersonalityCompiler.compile(...) → system_instruction 5-bloques
          └─▶ INSERT con is_active=true
  └─▶ UI invalida query "personality.active" → recarga ActiveState
```

### 5.3 Flujo clonación

```
User submits material (texto o archivo) en wizard
  └─▶ POST /api/v1/brand/personality/clone  multipart/form-data
      └─▶ [IMPL PENDING]  hoy retorna 501
          └─▶ Propuesta:
              1. ClonePipeline receives {text|file, tenant_id}
              2. run personality_app (LangGraph graph.py):
                 parser → janitor → psychologist → architect → embedder → simulator
              3. Persist PersonalityProfileModel: profile_type="cloned",
                 preset_key=null, qdrant_collection="personality_style_anchors",
                 anchor_count=N
              4. style_anchor_store.upsert_anchors(tenant_id, profile_id, messages)
              5. is_active=false hasta que user aprueba
  └─▶ UI Paso 3 muestra previa (Server Component lee el nuevo profile draft)

User click "Activar este estilo"
  └─▶ PUT /api/v1/brand/personality/{id}/activate  [NEW endpoint o reusa select-preset con profile_id]
      └─▶ activate(profile_id, tenant_id) → sets is_active=true, deactiva el anterior
```

**Nota sobre activate:** el endpoint actual `/select-preset` solo acepta `preset_key`. Agregar `POST /personality/{profile_id}/activate` (idempotente) como complemento, o extender `/select-preset` para aceptar `profile_id`. Propuesta: endpoint nuevo separado.

### 5.4 Flujo ajuste de dimensiones

```
User mueve slider energía 0.35 → 0.65
  └─▶ PUT /api/v1/brand/personality/{id}/dimensions  { dimensions: {energy: 0.65, ...} }
      └─▶ service.update_dimensions(profile_id, tenant_id, new_dimensions)
          ├─▶ PersonalityCompiler.compile(new_dimensions, patterns, exchanges)
          └─▶ UPDATE system_instruction, updated_at
  └─▶ UI invalida query y refresca sliders + ejemplos
```

Debounce sugerido en FE: 500ms tras el último cambio de slider. No necesitamos autosave-on-change instantáneo porque cada PUT recompila el `system_instruction` — suficiente con commit al soltar.

### 5.5 Flujo simular

```
User click "Probar en conversación" → "Generar respuesta"
  └─▶ POST /api/v1/brand/personality/{id}/simulate
      (hoy retorna 3 exchanges canned del profile)
      Futuro: LLM-driven simulation usando system_instruction + el mensaje del lead
```

### 5.6 Downstream (sales_agent, copy generators)

Hoy: consumidores leen `BrandIdentity.voice_tone` (string libre).

Después del cambio, consumidores migran a:

```python
# Ejemplo: sales_agent al construir su prompt
active_profile = await personality_port.get_active(tenant_id)
if active_profile:
    system_instruction = active_profile.system_instruction  # 5-bloques compiled
    # se concatena con strategy + audience layers (memoria: personality_engine_design 3-layer)
else:
    # fallback: string genérico "conversacional, cálido"
```

- Sales agent (`sales_agent` module): ya tiene guardrails wiring del commit `4402939d`. Agregar personality wiring en el mismo patrón — puerto `shared/links/ports/personality.py` (nuevo), llamado desde el graph de sales_agent al componer el system prompt.
- Landing copy generator: hoy lee `brand.voice_tone`. Cambiar a `personality.system_instruction`. Archivo candidato: `backend/src/modules/landing/application/services/*` (pendiente verificar con backend-expert).
- Asset captions: mismo patrón.

**BrandIdentity.voice_tone se mantiene en DB como legacy (nullable), pero ya no se lee ni se escribe desde UI.** Después de N sprints, migration para `DROP COLUMN` si nadie lee.

---

## 6. Journey Maps

### 6.1 Onboarding — nuevo tenant

```
Sign-up
  ↓
Brand Studio → Buyer personas        ✅
  ↓
Brand Studio → Identidad             ✅ (ya no pide voice_tone aquí)
  ↓
Brand Studio → Estilo Comunicacional ✅ [NEW]
  ├─ Elige preset (30 seg)    → Activa → Continúa
  └─ Clona (2-4 min)          → Previa → Activa → Continúa
  ↓
Brand Studio → Posicionamiento       ✅
  ↓ ...
```

**CTA sugerida tras completar Identidad:** card de completion que empuja al siguiente paso — "Tu marca ya tiene nombre. Ahora definí cómo habla → [Configurar estilo]".

### 6.2 Tenant existente con `voice_tone` cargado (migración)

```
Tenant abre /brand-studio/identity
  ↓
Schema ya no tiene voice_tone ni voice_tone_clone  ← hide fields
  ↓
BrandIdentity.voice_tone en DB sigue intacto (no se borra)
  ↓
Tenant abre /brand-studio/estilo
  ↓
Page detecta: no hay active PersonalityProfile PERO existe BrandIdentity.voice_tone no vacío
  ↓
Renderiza card de migración arriba del EmptyState:

  ┌────────────────────────────────────────────────────────────┐
  │ 💡 Tenés un tono de voz cargado desde antes:                │
  │                                                             │
  │ "Conversacional, cálido, con humor ligero"                  │
  │                                                             │
  │ ¿Querés que lo convirtamos en un estilo inicial? Vas a      │
  │ poder ajustarlo después.                                    │
  │                                                             │
  │ [ Convertir en estilo inicial ]   [ Empezar de cero ]       │
  └────────────────────────────────────────────────────────────┘

  "Convertir en estilo inicial":
    POST /api/v1/brand/personality/from-voice-tone
    → BE: heurística o LLM que mapea el string a dimensiones aproximadas +
      selecciona preset más cercano como base → crea PersonalityProfile
      con profile_type="migrated_from_voice_tone" → activate

  "Empezar de cero": oculta card, muestra EmptyState normal.
```

**Nota:** el endpoint `/from-voice-tone` es nuevo. Implementación sugerida: llamar al LLM con el string y pedir dimensions + preset más cercano; usar esto como base y permitir al tenant refinar.

La card se oculta permanentemente una vez que el tenant elige cualquiera de las dos opciones (persistir flag `voice_tone_migration_dismissed` en tenant metadata o `BrandSettings`).

### 6.3 Re-configuración — tenant cambia de estilo

```
Active profile: ☀️ Cálida y Cercana (preset)
  ↓
User click "Cambiar estilo" en header
  ↓
Dropdown: [Elegir otro preset] [Clonar uno nuevo] [Perfil custom desde cero]
  ↓
Elige "Clonar uno nuevo" → wizard 3 pasos
  ↓
Paso 3 previa → click "Activar este estilo"
  ↓
BE: deactivate "Cálida y Cercana" (soft, stays in history), activate clone
  ↓
UI refresca → nuevo profile activo
```

**Nota:** `DELETE /personality/{id}` ya existe. Pero para "historial" no borramos — solo `is_active=false`. Agregar vista opcional "estilos guardados" en futuro si hay demanda.

---

## 7. Gap Analysis

### 7.1 Orphaned rutas tras el cambio

| Ruta | Estado | Acción |
|---|---|---|
| `/brand-studio/identity?field=voice_tone` | Query `?field` ya no matchea un field real. UniversalEditableSection hace no-op (scroll a nada). | No breakage. Opcional: redirect server-side a `/brand-studio/estilo` si detecta `field=voice_tone` o `field=voice_tone_clone` para compatibilidad con enlaces viejos (emails, bookmarks). |
| `/brand-studio/identity?field=voice_tone_clone` | Idem. | Idem. |

### 7.2 Código huérfano (dead code cleanup)

| Artifact | Ubicación | Acción |
|---|---|---|
| `voice.schema.ts` | `frontend/src/features/brand-studio/schemas/voice.schema.ts` | **Delete.** Nadie lo importa tras el cambio. |
| `VoiceClonePlaceholder` | `frontend/src/features/brand-studio/actions/placeholders.tsx:25` | **Delete.** |
| `"voice-clone"` action key | `frontend/src/features/brand-studio/actions/registry.ts:30,57` | **Remove.** |
| `voice_tone_clone` field | `frontend/src/features/brand-studio/schemas/identity.schema.ts:64-70` | **Remove.** |
| `voice_tone` field | `frontend/src/features/brand-studio/schemas/identity.schema.ts:42-62` | **Remove.** |
| `BrandIdentity.voice_tone` column | `backend/src/modules/brand/domain/identity.py:110-113` | **Keep nullable, stop writing.** Drop en sprint futuro. |

### 7.3 Missing wiring (BE)

| Gap | Endpoint | Status |
|---|---|---|
| Clone pipeline | `POST /personality/clone` | Hoy retorna 501. Hay que cablear el LangGraph `personality_app` (parser→janitor→psychologist→architect→embedder→simulator) + persistir en `personality_profiles` + upsert anchors en Qdrant. |
| Activate específico | `POST /personality/{profile_id}/activate` | No existe. Necesario para activar perfiles clonados (select-preset solo maneja preset_key). |
| Migración legacy | `POST /personality/from-voice-tone` | No existe. Opcional si se decide ofrecer migración automática. |
| Port para sales_agent | `shared/links/ports/personality.py` | No existe. Crear paralelo al patrón guardrails. |

### 7.4 Accessibility / UX gaps

- Sliders de dimensiones necesitan labels accesibles (aria-label) + indicador numérico.
- Preset cards necesitan role="button" y foco visible (shadcn Card default no tiene).
- Clone wizard Paso 2 (loading 2-4 min) necesita mecanismo de **resumir** — si user cierra, poll en background + notificación cuando termine. Usar React Query con `refetchInterval` mientras hay job en curso, o Server-Sent Events si el backend lo soporta.

---

## 8. File Changes Required

### 8.1 Frontend

| File | Change |
|---|---|
| `frontend/src/features/brand-studio/lib/section-catalog.ts:34-48` | Insertar `{ slug: "estilo", label: "Estilo Comunicacional", icon: MessageCircle, kind: "singleton" }` en posición 3 |
| `frontend/src/features/brand-studio/pages/section-page-map.ts:32-46` | Agregar `estilo: CommunicationStylePage` |
| `frontend/src/features/brand-studio/pages/section-pages/` | **NEW** `CommunicationStylePage.tsx` (Server Component que fetcha `/personality/active` y renderiza Empty/Active) |
| `frontend/src/features/brand-studio/components/communication-style/` | **NEW folder** con: `EmptyState.tsx`, `ActiveState.tsx`, `DimensionsPanel.tsx`, `PresetPickerDrawer.tsx`, `PresetCard.tsx`, `CloneWizardDrawer.tsx`, `CloneStep1Material.tsx`, `CloneStep2Analyzing.tsx`, `CloneStep3Preview.tsx`, `SimulateDrawer.tsx`, `VoiceToneMigrationCard.tsx` |
| `frontend/src/features/brand-studio/api/personality-api.ts` | **NEW** fetchClient calls: `listPresets()`, `getActive()`, `selectPreset(key)`, `cloneFromMaterial(formData)`, `updateDimensions(id, dims)`, `simulate(id)`, `activate(id)`, `fromVoiceTone()` |
| `frontend/src/features/brand-studio/hooks/use-personality.ts` | **NEW** React Query hooks: `usePresets()`, `useActivePersonality()`, `useSelectPreset()`, `useClonePersonality()`, `useUpdateDimensions()`, `useSimulate()`, `useActivateProfile()` |
| `frontend/src/features/brand-studio/schemas/identity.schema.ts:42-70` | **Delete** `voice_tone` y `voice_tone_clone` fields |
| `frontend/src/features/brand-studio/schemas/voice.schema.ts` | **Delete file** |
| `frontend/src/features/brand-studio/actions/registry.ts:30,57` | **Remove** `"voice-clone"` action key + `VoiceClonePlaceholder` import |
| `frontend/src/features/brand-studio/actions/placeholders.tsx:25` | **Delete** `VoiceClonePlaceholder` |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/[section]/page.tsx` | Opcional: si `section === "identity"` y query tiene `field=voice_tone\|voice_tone_clone`, server redirect a `/brand-studio/estilo` |

### 8.2 Backend

| File | Change |
|---|---|
| `backend/src/modules/brand/api/personality.py:179-200` | **Implement** `POST /clone`: reemplazar 501 por wiring al LangGraph `personality_app`. Acepta text_input O file (multipart), invoca graph, persiste PersonalityProfileModel con is_active=false, upsert anchors en Qdrant, retorna DTO |
| `backend/src/modules/brand/api/personality.py` | **Add** `POST /{profile_id}/activate` — activa perfil existente (útil para clonados) |
| `backend/src/modules/brand/api/personality.py` | **Add** `POST /from-voice-tone` — toma `BrandIdentity.voice_tone` string → mapea a preset + dimensions via LLM → crea profile migrado |
| `backend/src/modules/brand/application/services/personality_service.py` | **Add** `clone_from_material(tenant_id, text_or_file) -> PersonalityProfile`, `activate(profile_id, tenant_id)`, `from_voice_tone(tenant_id, voice_tone_text)` |
| `backend/src/modules/brand/application/agents/style_analyzer/graph.py` | Verificar que `personality_app` está listo para invocación desde service; agregar adapter si hace falta |
| `backend/src/shared/links/ports/personality.py` | **NEW** port — expone `get_active(tenant_id) -> PersonalityProfileDTO | None` para consumidores cross-module (sales_agent, landing, assets) |
| `backend/src/modules/sales_agent/...` | Wire personality port en el graph paralelo al wiring de guardrails (commit `4402939d` es referencia) |
| `backend/tests/modules/brand/test_personality_api.py` | Tests: clone, activate, from_voice_tone, listings, guardrails, tenant isolation |
| `backend/tests/architecture/test_ddd_boundaries.py` | Verificar que el port se accede vía shared/links — no cross-module import directo |

### 8.3 Docs

| File | Change |
|---|---|
| `docs/domains/brand/communication-style.md` | **NEW** — documenta la sección, catálogo de presets, flujo de clonación, consumers downstream. |
| `.claude/rules/brand-personality.md` | **NEW opcional** — regla para que futuros Claude no dupliquen "voice" en otros schemas. |

---

## 9. New Components Required

| Component | Type | Location | Notes |
|---|---|---|---|
| `CommunicationStylePage` | Server Component | `features/brand-studio/pages/section-pages/` | Page root, fetcha `/personality/active`, decide Empty vs Active |
| `EmptyState` | Client | `features/brand-studio/components/communication-style/` | 2 cards CTA (preset / clone) + migration card si aplica |
| `ActiveState` | Client | idem | Dimensiones, huella, ejemplos, CTAs a probar/cambiar |
| `DimensionsPanel` | Client | idem | 6 sliders shadcn con labels ambas puntas, debounced PUT |
| `PresetPickerDrawer` | Client | idem | Drawer shadcn con 6 `PresetCard` en grid 2×3 |
| `PresetCard` | Client | idem | Card con icono, nombre, descripción, ejemplo, `Previa` + `Activar` |
| `CloneWizardDrawer` | Client | idem | Drawer con 3 pasos, state local (zustand o useReducer) |
| `SimulateDrawer` | Client | idem | Drawer con textarea + quick-context pills + respuesta |
| `VoiceToneMigrationCard` | Client | idem | Card one-time con 2 acciones, dismissible |

Todos los componentes respetan: Shadcn UI, Tailwind, español neutro LatAm (tuteo `tú`, sin voseo), design tokens Nicolify (`globals.css`).

---

## 10. Prototype Reference

**Omitido deliberadamente.** Los wireframes ASCII + FLOW-SPEC cubren la propuesta. Un prototipo HTML clickable agregaría valor si el alcance fuera cross-studio o si el usuario pidiera navegación; aquí es una sola sección con 4 estados contenidos.

Si aprobás la propuesta y querés HTML antes de implementar, avisame y genero `prototype/` con 5 páginas estáticas + sidebar.
