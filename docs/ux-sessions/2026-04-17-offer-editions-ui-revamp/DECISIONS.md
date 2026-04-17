# Decisions Log — Offer Editions UI Revamp

Session: `2026-04-17-offer-editions-ui-revamp`
Participants: Chris (founder) · ux-flow-architect skill
Scope: Revisión/rediseño visual del Offer Studio para Phases 5-10 del FLOW-SPEC de ediciones (2026-04-16). Input: `docs/flow-specs/FLOW-SPEC-offer-studio-editions.md`.

---

## D1 — Terminología: `Edición` (no `cohorte`)

**Decisión:** UI usa el término genérico "Edición" cross-archetype.
**Considerado:** Usar `edition_noun_es` del `ARCHETYPE_CATALOG` backend (cohorte/salida/convocatoria) por archetype. Rechazado por sobre-carga conceptual sin beneficio UX claro.
**Implicación backend:** `edition_noun_es` del catálogo queda disponible para contextos opcionales (subtítulo, descripción), no obligatorio en UI.
**Aplica en:** Sidebar rail, tab labels, breadcrumbs, botones, notificaciones.

---

## D2 — Tab bar del OfferShell: 4 tabs (no 5)

**Decisión:** `Info · Ventas · Assets · Campañas`.
**Considerado:**
- 5 tabs con "Conocimiento" separado → rechazado, se integra como sección 7 del tab Info.
- 5 tabs con "Analytics" → rechazado, analytics vive en Growth Studio.
- 6 tabs con "Landing" separado → rechazado, landing accedido vía split-button.

**Label + icono definitivo:**
| Tab | Icono | Label | Badge count |
|---|---|---|---|
| Info | 📋 | Info | (none) |
| Ventas | 💰 | Ventas | `(N)` = inscripciones de edición actual |
| Assets | 🎨 | Assets | `(N)` = assets de edición actual |
| Campañas | 📢 | Campañas | `(N)` = campañas asociadas a edición actual |

---

## D3 — Lista de ediciones: **rail permanente a la izquierda**

**Decisión:** Secondary left-rail entre el app sidebar y el main content, visible solo si `offer.has_editions === true`. Siempre muestra todas las ediciones agrupadas por estado (Próxima / Borradores / Pasadas) con la próxima destacada visualmente.

**Considerado:**
- Tab "Cohortes" dentro del shell → rechazado (rompe consistencia y obliga a sub-navegación redundante).
- Ruta hermana `/editions` sin rail → rechazado (forzaba más clicks y perdía contexto cross-edition).
- Modal/drawer → rechazado (no permanente).

**Comportamiento al cambiar de edición (click en rail):**
- La ruta cambia: `?edition={editionId}` (query param, no path) para mantener el tab activo.
- **Todos los tabs** (Info/Ventas/Assets/Campañas) se re-scopan a la edición seleccionada.
- El tab activo NO cambia (si estabas en Ventas y switchás a Edición #2, ves Ventas de #2).
- Estado read-only automático cuando `edition.status === COMPLETED` o `CANCELLED`.

**Offers sin ediciones (PRODUCTO / MEMBRESIA):** rail oculto, main ocupa todo el ancho. Mismo set de tabs, pero Info sin sección "Fechas y Logística" ni "Pricing Tiers" — en su lugar "Acceso y Entrega" + precio único.

---

## D4 — Rail colapsable con badges numéricos

**Decisión:** Rail colapsable con botón `‹‹`. Estado colapsado muestra círculos con el número de edición (`#3`, `#2`, etc.) con coloring semántico.

**Considerado:**
- No colapsable → rechazado (quita demasiado espacio en pantallas chicas).
- Auto-colapsado si > 5 ediciones → rechazado por inconsistencia.

**Visual en colapsado:**
- Edición próxima: círculo azul fill con ring
- Borradores: círculo con borde dashed amber
- Pasadas: círculo gris 100
- Botón `+` al final con borde dashed morado

**Ancho:**
- Expandido: `240px` (w-60)
- Colapsado: `56px` (w-14)

---

## D5 — Info tab repite todo por edición (no shared/scoped)

**Decisión:** Cada edición tiene su propia copia completa de todos los campos. Sin distinción "campos compartidos vs scoped". El flujo primario de creación de nuevas ediciones es **clonar desde una anterior** (literal / con cambio de fechas / regenerado con IA).

**Rationale:** simplifica modelo mental. Usuario piensa "mi edición #3 tiene X fechas, Y precios, Z deliverables" sin preocuparse por qué campo se propaga y cuál no.

**Implicación backend:** ya resuelto por `LaunchEdition` + `edition_clone_service` de Phase 3. Cada edición guarda todo. Reads de Info tab apuntan a la edición seleccionada.

**Implicación UX:**
- Crear primera edición = wizard copilot completo.
- Crear edición N>1 = modal "Clonar desde..." con strategy picker (literal / fechas / IA regenera).

---

## D6 — Landing: split-button al nivel del tab bar (estilo Webflow)

**Decisión:** Botón combinado con main action `🌐 Editar landing` y dropdown `▾` con acciones secundarias. Color emerald (verde, sugiere "publicado/activo"). Se posiciona a la derecha del tab bar, en la misma fila.

**Estados del main button (dinámicos):**
| Estado landing | Label | Color |
|---|---|---|
| No existe | "Generar landing con IA" | morado (acción inicial) |
| Borrador (no publicado) | "Publicar landing" | ámbar |
| Publicada con cambios sin guardar | "Publicar cambios" | emerald |
| Publicada sin cambios | "Editar landing" | emerald |
| Generando/publicando | "Procesando..." | gris + spinner |

**Menú dropdown (siempre disponible si landing existe):**
- 👁 Abrir URL pública (nueva pestaña)
- 📋 Copiar URL
- 🔄 Regenerar con IA
- 📥 Clonar de otra edición
- ⏸ Despublicar (amber text)

**Click principal:** abre `offer-landing-editor.html` equivalente (ruta `/offer-studio/offer/[id]/editions/[editionId]/landing` o similar) en **nueva pestaña/ventana** (`target="_blank"`). El editor es full-screen (sin app sidebar ni rail).

**Offer sin ediciones:** edita la landing del offer (única). Misma mecánica, sin rail.

---

## D7 — Tab Campañas = listado read-only desde Growth Studio

**Decisión:** Campañas mostradas = una campaña es **un flight en una plataforma** (Opción A de las tres interpretaciones). Ej: "MasterClass Jul — Tráfico" es una campaña Meta Ads; "Copywriting search PE" es otra campaña Google Ads. No hay "launch container multi-canal".

**Fuente de datos:** El listado viene de Growth Studio (campañas que el usuario asoció a esta edición vía UI de Growth Studio — ya existe `OfferReassignPopover`).

**Scope del tab en Offer Studio:**
- Lista campañas asociadas.
- KPI strip simple (inversión, leads, CPA, ROAS).
- Cada card linkea a Growth Studio para análisis profundo.
- Botón "+ Asociar campaña existente" → navega a Growth o abre modal con lista filtrada.

**Lo que NO se hace acá:**
- Configurar budget / audience / creatives.
- Ver detalle de analytics (eso es Growth).
- Editar ad copy.

**Placeholder para canales no-pagos (email, IG orgánico):** banner inferior sugiriendo "configurar desde Growth Studio" — deferido a fase futura.

---

## D8 — Copilot interview obligatorio al crear offer

**Decisión:** No hay toggle "interview vs focus" al crear una oferta nueva. Siempre se abre el flujo conversacional con IA. En el último bloque (después de extraer toda la info base), copilot pregunta obligatoriamente "¿cuándo tu primera edición?".

**Quick-replies del bloque:**
- `📅 Fecha propuesta por IA` (ej "El 15 de julio" si el contexto lo sugiere)
- `📅 Elegir fecha…` (date picker)
- `🤷 Todavía no sé`

**Comportamiento:**
- Si usuario da fecha → edición creada con `status=UPCOMING + visibility=PUBLIC`.
- Si skip → edición se queda `DRAFT + PRIVATE` con placeholder (como hoy). Copiloto explica: leads van a waitlist mientras no haya fecha.

**Implementación:** extender `offer_config.py` interview con un bloque de fecha al final del wizard. Split view (chat + preview en vivo de la edición que se va a crear).

---

## D9 — Ventas tab = listado simple, detalle en Closer Studio

**Decisión:** El tab Ventas muestra un listado mínimo de inscripciones (contacto, estado, tier, monto, pagado, origen). Gestión operativa avanzada (pausar agente, reasignar, timeline de mensajes) vive en **Closer Studio > Inscripciones** (nueva ruta).

**Vista global:** nueva ruta `/sales/enrollments` (NEW sidebar entry bajo Closer Studio) que lista **todas** las inscripciones cross-ofertas con filtros: oferta × edición × estado × tier × canal-origen. Grupos visuales por (Oferta + Edición) y un grupo aparte "Lista de espera" con bulk-action "Notificar a todos".

**Racional:** evita duplicar UI. Offer-centric view = contexto cohorte. Closer-centric view = operativo diario.

---

## D10 — Assets tab = placeholder para Canva-clone (diferido)

**Decisión:** Tab Assets tiene estructura funcional (gallery filtrable + clone-from-previous + generate-with-IA) pero el editor inline de assets se difiere a **Fase 2** como "editor visual tipo Canva". Por ahora:
- Listado con thumbnails y filtros por tipo (flyers, reels, carruseles).
- Click en asset → abre editor en nueva pestaña (stub: mensaje "Próximamente").
- Botón "Generar con IA" → pipeline ya pensado (no detallado en esta sesión).
- Botón "Jalar de Edición #N" → usa `edition_clone_service` ya implementado en Phase 3.

**Nota:** los assets se cachean automáticamente al crear una edición clonando la anterior (con substitución de tokens `{start_date}`, `{price}`, etc.).

---

## D11 — Sidebar global: nueva entrada bajo Closer Studio

**Decisión:** Agregar `Inscripciones` como ítem bajo Closer Studio en `AppSidebar.tsx`, con badge `NEW` temporal (6 meses).

**Posición:** entre "Contactos" y el final del grupo.

**Ruta:** `/sales/enrollments`.

**Icono:** `ClipboardList` (Lucide) o `Users` variant.

---

## D12 — Analytics sale del Offer Studio

**Decisión:** Phase 10 del FLOW-SPEC original pedía "per-edition analytics compare" como tab dentro del offer. **Eliminado**. La comparación y analytics avanzada vive en Growth Studio. El Offer Studio solo muestra KPIs mínimos (ocupación, revenue) en tab Info y Ventas.

**Implicación para Phase 10:** renombrado internamente a "Growth Studio — Per-Edition Analytics Views". Fuera del alcance visual de esta sesión pero reconocido en PLAN.md.

---

## D13 — Waitlist banner: siempre visible si waitlist > 0

**Decisión:** Banner arriba del contenido del tab (debajo del tab bar) con purple/accent gradient. Visible cuando `edition.visibility === PUBLIC && offer.waitlist_count > 0`.

**Contenido:**
- Icono clipboard + texto "Tienes N leads en lista de espera para esta oferta"
- Subtítulo explicativo
- Botones: "Ver lista" (secundario) + "Notificar a todos" (primario)

**Acción "Notificar a todos":** dispara `promote_waitlist_to_edition` (tool de Phase 6) → envío masivo por canal preferido de cada contact.

**Dismissable:** NO (el banner es informativo, no debe ocultarse manualmente; desaparece cuando waitlist=0 o cuando se ejecuta notificación).

---

## D14 — Versionado visual: colores semánticos por estado edición

**Decisión fija:** paleta de status badges + border patterns.

| Estado edición | Badge color | Border left card | Rail entry |
|---|---|---|---|
| DRAFT (placeholder) | ámbar soft, dashed border | amber dashed | border dashed amber |
| DRAFT (usuario rellenó) | ámbar soft | amber solid | fondo amber soft |
| UPCOMING | azul soft | azul solid | fondo azul + ring |
| ACTIVE | emerald soft | emerald solid | fondo emerald + ring |
| COMPLETED | gris 100 | gris solid | fondo slate 100 |
| CANCELLED | rojo soft | rojo solid | opacity 40 |

**Visibility badge** (al lado del status):
- 🔒 PRIVATE: bg slate 100
- 🌐 PUBLIC: bg purple soft

**Pricing tier timeline colors:**
- early_bird: emerald
- regular: blue
- last_call: amber

---

## Resumen (iteración 1)

Fueron 14 decisiones en esta sesión. Todas documentadas, sin ambigüedad. El prototipo HTML en `prototype/` implementa visualmente cada una de estas decisiones y es la referencia normativa para la implementación.

---

# Iteración 2 — Correcciones Post-Implementación (2026-04-17, tarde)

Contexto: Phase 9a part 1 + Phase 9b lite shipeadas. Al revisar el offer detail en dev-app con `has_editions=true`, se detectan problemas que invalidan parcialmente D2, D3 y D4. Chris pide reset de modelo mental sobre cómo el offer maneja ediciones visualmente.

Prototipos `-v2.html` reemplazan a los originales como referencia normativa en adelante.

## D15 — Rail full-height eliminado (reversión parcial de D3)

**Decisión:** El rail permanente a la izquierda (`EditionsRail.tsx` + `EditionsRailCollapsed.tsx`) se **elimina**. En su lugar:

1. **Header offer persistente** arriba de todo (título, archetype, autosave, kebab, status global) — existe sin contaminación por edición.
2. **Tab bar** debajo del header — tabs = offer-level concept.
3. **EditionSelectorBar** (componente nuevo) — aparece solo debajo del tab bar cuando el tab actual tiene contenido edition-scoped (Ventas, Assets, Campañas). Dropdown + badges + CTAs.
4. **EditionsManagementSection** — management panorámico de ediciones vive como última sub-sección del tab Info (cards completas con KPIs, acciones, agrupadas por status). Reemplaza la gestión que antes hacía el rail y la actual "Ediciones" sección suelta.

**Rationale:** la solución con rail duplicaba el concepto "edición" (rail + sección Editions en Info), ocupaba alto completo junto al header creando inconsistencia visual (título aparecía 2 veces), y forzaba estado colapsado/expandido que el usuario no usa. Edition selector por tab es más honesto: Info es offer-level, los otros tabs son edition-scoped y muestran el selector solo cuando hace falta.

**Preserva de D3:**
- Agrupación por estado (En curso / Próxima / Borradores / Pasadas).
- Coloring semántico per-status (D14 sigue vigente).
- Switch vía `?edition=` query param.
- `has_editions=false` oculta el selector (archetypes PRODUCTO / MEMBRESIA).

**Anula de D3:**
- Rail permanente entre app sidebar y main.
- Variante colapsada con badges circulares.
- Footer "+ Nueva edición" en rail.

**Invalida D4:** variante colapsada ya no aplica — no hay rail para colapsar.

---

## D16 — Management panorámico de ediciones = última sección del Info tab

**Decisión:** La gestión CRUD de ediciones (listar, crear, editar, clonar, publicar, despublicar, cancelar) vive como última sección del Info tab cuando `offer.has_editions === true`. Solo renderiza si aplica — invisible para PRODUCTO / MEMBRESIA.

**Visual:** Cards por edición agrupadas por status. Cada card muestra header (`#N · fecha · status · visibility`), KPIs (ocupación / revenue / días), acciones inline (Editar, Clonar, Publicar/Despublicar, Cancelar), y CTA prominente al final: `+ Nueva edición`. Sigue el color system de D14.

**Empty state:** mensaje "Aún no creaste ediciones" + botón grande "Crear primera edición" que abre `EditionFormDialog`.

**Reemplaza:**
- `EditionsSection.tsx` actual (listado suelto sin context).
- El rail como management entrypoint.

**Conserva comportamiento del tab:** el Info tab en sí sigue siendo offer-level. Esta sub-sección es gestión de ediciones, no contenido de una edición — editar detalles de la edición N abre `EditionFormDialog` modal.

---

## D17 — Galería Visual se mueve de Info a Assets (revierte posición en builder-config)

**Decisión:** La sección `gallery` sale del Info tab. Su contenido (`GalleryManager` + `GalleryPreview`) pasa a ser parte del Assets tab como zona "Galería de Oferta" (offer-level, compartida entre ediciones).

**Rationale:** galería = fotos/assets visuales del offer. Conceptualmente encaja en Assets, no en Info. Info debe ser metadata (identidad, promesa, estrategia, precios, etc.), no assets.

**Implicación código:**
- Quitar `"gallery"` de todos los arrays en `ARCHETYPE_BUILDER_CONFIG` (`offer-builder-config.ts:207-274`).
- Assets tab integra `GalleryManager` como primera sub-zona, seguida de "Assets por Edición" (gallery per-edition: flyers, reels, carruseles).

**No afecta backend:** el modelo Gallery no cambia. Es sólo re-ubicación frontend.

---

## D18 — Conocimiento permanece como sección dentro de Info (confirma D2)

**Decisión:** Conocimiento (RAG del agente) es la penúltima sección del Info tab (antes de la sub-sección Ediciones cuando aplica). Ya no hay tab "Conocimiento" separado.

**Rationale:** D2 original pedía 4 tabs (Info · Ventas · Assets · Campañas). Phase 9b lite preservó temporalmente un 5to tab "Conocimiento" para evitar un estado intermedio destructivo. Esta iteración elimina esa temporal: Conocimiento migra a sección del Info (reutiliza el componente Knowledge actual).

**Implicación código:**
- Eliminar ruta `app/.../offer/[id]/knowledge/page.tsx` (del PLAN original).
- Integrar `KnowledgeView` como section dentro de `OfferInfoTab`.
- Tab bar pasa de 5 a **4 tabs**: Info · Ventas · Assets · Campañas.

---

## D19 — Botón "+ Nueva edición" conecta a `EditionFormDialog` existente (clone modal diferido)

**Decisión:** En esta iteración el CTA "+ Nueva edición" (tanto en `EditionSelectorBar` como en `EditionsManagementSection`) abre `EditionFormDialog` (que ya existe en `components/editions/EditionFormDialog.tsx`). NO se implementa `EditionCloneModal` con strategy picker aún — se difiere a iteración futura.

**Rationale:** `EditionFormDialog` cubre "crear nueva edición desde cero" (fechas, pricing override, capacity). `EditionCloneModal` con strategy `literal/date_replace/ai_regen` (D7 fase original) es superior UX pero requiere:
- Extender endpoint `/editions/{source_id}/clone` con payload de strategy.
- Implementar AI regen path.
- Nuevo componente.

Ship incremental: conectar el botón ahora (deshacer el `console.info` stub) usando lo existente, luego upgrade a clone modal en una fase posterior.

**Implicación código:**
- `OfferShell.tsx` → reemplazar `openCloneModal` no-op por state `<EditionFormDialog>` controlled.
- `EditionsRail.tsx` + `EditionsRailCollapsed.tsx` → se **eliminan** (D15).
- `EditionSelectorBar.tsx` (nuevo) → prop `onCreateNew` llama openFormDialog del shell.

---

## D20 — Título offer único en Row1, contexto edición en el selector bar

**Decisión:** El título principal (`<h1>` en `OfferShellHeaderRow1`) muestra solo el nombre del offer + archetype + autosave. **No** incluye sufijo "· Edición #N · fecha" como pide el UI-SPEC v1.

**Rationale:** mostrar la edición en el header global obliga a re-fetch/refresh del header con cada switch de edición, y confunde porque el header es persistente. El contexto de edición vive 100% dentro del `EditionSelectorBar`, donde sí es útil (dropdown muestra cuál activa, badges status+visibility).

**Header resultante:**
```
┌─────────────────────────────────────────────────────────┐
│ ← MasterClass de Copywriting             [● Borrador]   │
│   Programa · DWY · ● Guardado hace 2s    [⋮]            │
└─────────────────────────────────────────────────────────┘
```

Status/visibility badges del header son **offer-level** (lifecycle estado del offer, no de la edición).

**Progreso:** la barra `78% · 8/10 · siguiente: X` sigue en Row2. Pero ahora siempre muestra progreso offer-level (completitud del template del offer), no progreso por edición. Si usuario switchea edición, el % no cambia. Una edición tiene su propia completitud visible como badge en `EditionSelectorBar` (`Edición #3 · 85% · Próxima`), no como barra.

**Reemplaza en D14/D3:** banner "viendo edición pasada · read-only" ya no vive en Row1 como sufijo — ahora es un banner explícito debajo del `EditionSelectorBar` cuando la edición actual es COMPLETED/CANCELLED.

---

## Matriz: tabs × scope × selector visibility

| Tab | Scope | EditionSelectorBar visible | Notas |
|---|---|---|---|
| Info | **Offer-level + sub-sección management** | NO | Contenido es del offer. Sub-sección final gestiona todas las ediciones. |
| Ventas | Edition-level | SÍ | KPIs + enrollments de edición activa. |
| Assets | Mixto (zona oferta + zona edición) | SÍ | Selector filtra zona per-edition. Galería offer-level siempre visible. |
| Campañas | Edition-level | SÍ | Campaign cards asociadas a edición activa. |

Cuando `offer.has_editions === false`:
- Info sigue igual pero sin sub-sección management.
- Ventas/Assets/Campañas **no muestran** `EditionSelectorBar` — son directamente offer-level.

---

## Resumen iteración 2

6 decisiones de corrección (D15-D20). Invalidan parcialmente D2-D4 pero preservan D5-D14. Prototipos `-v2.html` reemplazan a originales. Implementación = 1 fase nueva "Phase 9a.1 — Shell Correction" documentada en PLAN.
