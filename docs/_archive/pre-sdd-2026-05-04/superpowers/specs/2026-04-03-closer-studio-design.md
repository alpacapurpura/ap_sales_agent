# Closer Studio — Design Spec

**Fecha:** 2026-04-03
**Autor:** Claude + Chris
**Modulo:** `sales_agent` (backend) + `closer-studio` (frontend feature)
**Estado:** Draft — pendiente aprobacion

---

## 1. Contexto y Motivacion

Nicolify automatiza ventas mediante un AI Sales Agent (LangGraph) que opera autonomamente en multiples canales (IG DM, WhatsApp, Telegram, ManyChat). Hoy el dueno del negocio **no tiene visibilidad ni control** sobre estas conversaciones en tiempo real.

**Problema:** El owner no puede:
- Ver que conversaciones estan calientes y cuales se estan enfriando
- Detectar cuando el AI no esta manejando bien una situacion
- Tomar control de una conversacion para responder personalmente
- Reactivar conversaciones que se congelaron sin accion
- Ver el perfil completo de un lead cruzando todas sus interacciones
- Dar instrucciones especificas al AI sobre como manejar un lead

**Solucion:** Closer Studio — un dashboard de supervision y gestion de conversaciones inspirado en Chatwoot pero disenado para un paradigma AI-first donde el agente opera autonomamente y el humano supervisa e interviene cuando lo detecta necesario.

**Resultado esperado:** El owner abre Closer Studio y en <5 segundos sabe: cuantas conversaciones hay activas, cuales estan calientes, cuales necesitan atencion, y puede intervenir en cualquiera con un click.

---

## 2. Usuarios y Roles

| Rol | Descripcion | Acceso |
|---|---|---|
| **Owner** | Dueno del negocio. Supervisa, interviene, da instrucciones. | Completo |
| **AI Sales Agent** | Agente autonomo que maneja conversaciones. | No accede al UI (es el operador supervisado) |
| **Lead/Contacto** | Persona que interactua por IG/WA/TG. | No accede al UI (interactua por canal) |
| **Copilot** | Asistente in-app que navega al owner a acciones especificas. | Lee URLs deep-linked |

---

## 3. Arquitectura de Vistas

**Patron:** Hybrid Routing — rutas Next.js para code-splitting + Zustand store para estado compartido entre vistas.

```
/[tenantId]/sales/studio/
  layout.tsx        -- Tab navigation (Inbox | Pipeline | Congeladas) + KPI bar
  page.tsx          -- Redirect a /inbox
  inbox/page.tsx    -- Vista 3-panel (lista | thread | contacto)
  pipeline/page.tsx -- Kanban board
  frozen/page.tsx   -- Conversaciones congeladas con diagnostico AI
```

**Zustand store** mantiene: `selectedLeadId`, `filters`, `inputMode`, `unreadByLead`, `wsConnected`, `sidebarOpen`. Persiste entre cambios de ruta.

---

## 4. Maquetas Aprobadas

Las siguientes maquetas HTML fueron aprobadas por el usuario:

| Maqueta | Ubicacion | Contenido |
|---|---|---|
| Feature Map | `.superpowers/brainstorm/.../01-feature-map.html` | 45 funcionalidades en 8 areas |
| Enfoques Arquitectura | `.superpowers/brainstorm/.../02-approaches.html` | 3 opciones → usuario eligio C (Hibrido) |
| **Inbox 3-Panel** | `.superpowers/brainstorm/.../03-inbox-wireframe.html` | Layout completo full-width con datos reales |
| **Pipeline + Congeladas** | `.superpowers/brainstorm/.../04-pipeline-frozen.html` | Kanban 6 columnas + diagnostico AI |

Estas maquetas son la **referencia visual definitiva** para la implementacion.

---

## 5. Historias de Usuario y Criterios de Aceptacion

### EPIC 1: Supervision de Conversaciones (Inbox)

---

#### US-1.1: Ver lista de conversaciones activas

**Como** owner, **quiero** ver todas las conversaciones activas en una lista lateral, **para** tener una vision rapida de toda mi operacion de ventas.

**Criterios de aceptacion:**
- [ ] La lista muestra TODAS las conversaciones con `is_active=true` del tenant
- [ ] Cada item muestra: avatar con iniciales, nombre del lead, preview del ultimo mensaje (truncado a 1 linea), timestamp relativo ("hace 3m"), badge de canal (IG/WA/TG/Web), indicador de temperatura (dot color: rojo=hot, amarillo=warm, azul=cold), chip de etapa del funnel (Nuevo/Calificando/Negociando/Cita/Cerrado), badge de handler (🤖 AI / 👤 Tu / ⚠️ Escalada), contador de mensajes no leidos
- [ ] Conversaciones escaladas tienen borde izquierdo rojo y aparecen primero
- [ ] La lista hace scroll virtual (no carga todas de golpe si hay >100)
- [ ] Ordenamiento por defecto: escaladas primero, luego por ultima actividad descendente
- [ ] Click en un item lo selecciona (highlight con borde violeta) y abre el thread en el panel central
- [ ] El item seleccionado persiste si cambio a Pipeline y vuelvo a Inbox (Zustand)
- [ ] La URL se actualiza: `?lead={leadId}` al seleccionar

**Datos del backend:**
- Endpoint: `GET /api/v1/closer-studio/conversations`
- Respuesta incluye: `lead_id`, `display_name`, `channel`, `temperature`, `lead_score`, `handler_mode`, `last_message_preview`, `last_message_at`, `unread_count`, `pipeline_stage`, `funnel_stage`

---

#### US-1.2: Filtrar conversaciones

**Como** owner, **quiero** filtrar la lista por temperatura, canal, handler y estado, **para** enfocarme rapidamente en lo que importa.

**Criterios de aceptacion:**
- [ ] Fila de chips debajo del search: Todas | 🔴 Hot | 🟡 Warm | 🔵 Cold | 🤖 AI | 👤 Humano | ⚠️ Escaladas
- [ ] Click en un chip lo activa (highlight). Solo un filtro de temperatura activo a la vez.
- [ ] Los filtros se reflejan en la URL: `?filter=hot&handler=ai`
- [ ] Al activar un filtro, la lista se actualiza inmediatamente (React Query refetch con nuevo filtro)
- [ ] Un chip "Todas" limpia todos los filtros
- [ ] El contador total cambia segun filtro activo

---

#### US-1.3: Buscar conversaciones

**Como** owner, **quiero** buscar por nombre de lead, contenido de mensaje o producto, **para** encontrar una conversacion especifica rapidamente.

**Criterios de aceptacion:**
- [ ] Input de busqueda en la parte superior del panel izquierdo con placeholder "Buscar conversacion... (⌘K)"
- [ ] Busqueda con debounce de 300ms
- [ ] Busca en: nombre del lead, contenido de mensajes, producto asociado
- [ ] Resultados reemplazan la lista filtrada
- [ ] `⌘K` / `Ctrl+K` abre/enfoca el input desde cualquier parte del Studio
- [ ] Limpiar el input restaura la lista original con filtros activos

---

#### US-1.4: Ver thread completo de una conversacion

**Como** owner, **quiero** ver todos los mensajes de una conversacion en orden cronologico, **para** entender el contexto completo de la interaccion.

**Criterios de aceptacion:**
- [ ] Panel central muestra el thread completo de la conversacion seleccionada
- [ ] Header del thread muestra: avatar, nombre, badge de handler activo (🤖 AI Activo / 🛑 Pausado por ti), canal, transicion de etapa ("Negociando → Cita")
- [ ] Mensajes con burbujas diferenciadas por `sender_type` + `sender_source`:
  - Lead (USER): burbuja oscura, alineada a la derecha
  - AI (ASSISTANT, sender_source=auto): burbuja violeta, alineada a la izquierda, con icono 🤖
  - Humano (ASSISTANT, sender_source=human_direct): burbuja verde, alineada a la izquierda, con icono 👤
  - Sistema (SYSTEM): banner centrado con fondo sutil, texto gris
  - Instruccion (SYSTEM, sender_source=human_instruction): banner con borde violeta "🎯 Instruccion del owner: ..."
- [ ] Cada mensaje muestra timestamp + canal (si multi-canal)
- [ ] Eventos del sistema intercalados: cambios de temperatura, senales de compra, escalaciones, cambios de handler
- [ ] **AI Reasoning** expandible debajo de cada mensaje del AI: muestra la estrategia del agente ("Closing: Detecto buying signal, redirigir a cita"). Colapsado por defecto, click para expandir.
- [ ] Auto-scroll al ultimo mensaje al abrir. Scroll manual disponible para historial.
- [ ] Paginacion de mensajes: carga los ultimos 50 al abrir, scroll up para cargar mas (cursor pagination con `before` timestamp)

**Decision de implementacion:** Los eventos del sistema (cambios de temperatura, senales) son `messages` con `sender_type=SYSTEM`. El AI reasoning viene del campo `metadata_info` del mensaje del AI (ya existe en el modelo).

---

#### US-1.5: Ver panel de contacto (sidebar derecho)

**Como** owner, **quiero** ver toda la informacion del lead/contacto al lado de la conversacion, **para** tener contexto completo sin salir del Studio.

**Criterios de aceptacion:**
- [ ] Panel derecho (~300px) muestra el perfil completo del lead seleccionado
- [ ] **Header**: Avatar, nombre, descripcion corta (negocio + tiempo), badges de todos los canales conectados (IG, WA, TG)
- [ ] **Scoring visual**: 3 anillos circulares (Fit Score 0-100, Intent Score 0-100, Temperatura con emoji)
- [ ] **Lifecycle bar**: Barra de progreso horizontal con etapas (Lead → MQL → SQL → Opportunity → Customer). Etapa actual resaltada en amarillo, anteriores en violeta.
- [ ] **Datos del contacto**: Nombre, negocio, industria, etapa del negocio, pain point principal, producto de interes. Campos obtenidos de `profile_data` (UserProfile).
- [ ] **Calificacion AI**: Autoridad (dueño/empleado/otro), tier financiero, urgencia, objeciones activas. Datos de `qualification_answers` del checkpoint.
- [ ] **Historial de interacciones**: Timeline cronologico de TODAS las interacciones del contacto (cross-canal). Items: fecha + descripcion del evento (mensaje, visita, cita, compra).
- [ ] **Productos explorados**: Tags de productos por los que el lead pregunto, con estado (activo/descartado).
- [ ] **Notas del owner**: Textarea editable. Se guarda con debounce al escribir. Campo `custom_system_instruction` o nuevo campo en lead.
- [ ] **Boton "Ver perfil completo"**: Navega a `/sales/contactos/{leadId}`
- [ ] El panel es colapsable (toggle con icono). Estado persiste en Zustand.

**Decision de implementacion:** El historial cross-conversacion se obtiene de `journey_events` (CRM) + `messages` agrupados. Los productos explorados se infieren del campo `active_product` en checkpoints historicos.

---

#### US-1.6: Indicadores de conversaciones no leidas

**Como** owner, **quiero** ver cuales conversaciones tienen mensajes nuevos que no he visto, **para** priorizar mi atencion.

**Criterios de aceptacion:**
- [ ] Badge circular violeta con numero en la esquina de cada item con mensajes no leidos
- [ ] Items con no leidos tienen background ligeramente diferente (`rgba(139,92,246,0.05)`)
- [ ] Al abrir una conversacion (click en lista), su `unread_count` se resetea a 0 (llamada API)
- [ ] El WebSocket incrementa `unread_count` en el Zustand store al recibir `new_message` events
- [ ] El contador total de no leidos aparece en el tab "Inbox" del sidebar de la app

---

### EPIC 2: Control de Conversaciones (STOP / RESUME / Instrucciones)

---

#### US-2.1: Pausar el AI en una conversacion (STOP)

**Como** owner, **quiero** pausar el Sales Agent en una conversacion especifica, **para** tomar control y responder yo mismo.

**Criterios de aceptacion:**
- [ ] Boton "🛑 STOP AI" visible en el header del thread cuando `handler_mode=ai`
- [ ] Click abre confirmacion: "Vas a pausar el AI en esta conversacion. Los mensajes del lead seguiran llegando pero el AI no respondera."
- [ ] Al confirmar:
  - API call: `POST /conversations/{leadId}/stop`
  - `handler_mode` cambia a `human` en checkpoint
  - `paused_at` = timestamp actual
  - Header del thread cambia a "🛑 Pausado por ti"
  - Boton cambia a "▶️ Reanudar AI"
  - Badge en la lista cambia de "🤖 AI" a "👤 Tu"
  - Evento del sistema aparece en el thread: "🛑 [Owner] tomo control de la conversacion"
- [ ] Mientras esta pausado: los mensajes del lead llegan y se muestran en el thread (via WebSocket), pero el AI NO responde
- [ ] Si el lead escribe mientras esta pausado, el owner recibe notificacion visual (badge + pulso)

**Decision de implementacion:** El flag `handler_mode` se verifica en `ChatOrchestrator.process_chat_flow()` ANTES de invocar el grafo LangGraph. Si `handler_mode='human'`, el mensaje se almacena pero el grafo NO se ejecuta. Se emite evento WS `new_message`.

**Race condition handling:** Si el AI esta mid-execution cuando se hace STOP, se verifica `handler_mode` OTRA VEZ en `OutputManager.process_response()` antes de enviar al canal. Si cambio a `human`, el response del AI se almacena como draft pero NO se envia.

---

#### US-2.2: Enviar mensaje directo al lead

**Como** owner (con AI pausado), **quiero** escribir un mensaje que llegue directamente al lead por su canal, **para** responder personalmente a su consulta.

**Criterios de aceptacion:**
- [ ] Input area en la parte inferior del thread con toggle: "💬 Mensaje directo" | "🤖 Instruccion al AI"
- [ ] En modo "Mensaje directo":
  - Placeholder: "Escribe tu mensaje al lead..."
  - Boton: "Enviar mensaje"
  - Al enviar:
    - API call: `POST /conversations/{leadId}/messages` con `mode=direct`
    - El mensaje se envia al lead por el mismo canal (IG/WA/TG) usando el channel adapter correspondiente
    - El mensaje aparece en el thread como burbuja verde (humano) con icono 👤
    - Se almacena con `sender_source=human_direct`
  - Soporte para Enter para enviar, Shift+Enter para nueva linea
  - Textarea auto-resize
- [ ] Si el canal no soporta envio bidireccional (aun), mostrar mensaje: "Envio directo no disponible para [canal]. Usa el modo Instruccion al AI."
- [ ] El mensaje directo funciona tanto con AI pausado como activo

**Decision de implementacion:** El `ChannelResolver` resuelve el adapter correcto a partir del canal del ultimo mensaje del lead + credenciales de `ChannelConnectionModel`. El `channel_user_id` es el `telegram_id`, `whatsapp_id`, o `instagram_id` del lead.

---

#### US-2.3: Dar instruccion al AI

**Como** owner, **quiero** darle una instruccion especifica al Sales Agent sobre como manejar esta conversacion, **para** guiar su comportamiento sin tener que responder yo mismo.

**Criterios de aceptacion:**
- [ ] En modo "🤖 Instruccion al AI":
  - Placeholder: "Ej: 'Ofrece horarios de manana, menciona que el coach tiene experiencia en RRHH'"
  - Boton: "Enviar instruccion"
  - Hint debajo: "El AI incorporara esta instruccion en su proximo mensaje al lead"
  - Al enviar:
    - API call: `POST /conversations/{leadId}/messages` con `mode=instruction`
    - Se almacena en `messages` como `sender_source=human_instruction` (visible en audit trail)
    - Se almacena en `checkpoint.resume_objective`
    - Aparece en el thread como banner violeta: "🎯 Instruccion: [texto]"
    - En el proximo mensaje del lead, el AI lee la instruccion como directriz
- [ ] La instruccion es de un solo uso (se consume al usarse). Si quiere dar otra, escribe otra.
- [ ] Si no hay interaccion del lead despues de la instruccion, el owner puede hacer "nudge" (ver US-2.4)

**Decision de implementacion:** La instruccion se inyecta en el `AgentState` como mensaje de sistema con prefijo `[INSTRUCCION DEL OPERADOR]` antes de invocar el grafo. El prompt del supervisor debe reconocer y priorizar estas instrucciones. Despues de inyectarla, `resume_objective` se limpia (one-shot).

---

#### US-2.4: Hacer que el AI envie mensaje proactivamente (Nudge)

**Como** owner, **quiero** hacer que el AI envie un mensaje al lead ahora mismo basado en mi instruccion, sin esperar a que el lead escriba primero, **para** reactivar una conversacion o ejecutar una accion inmediata.

**Criterios de aceptacion:**
- [ ] Boton "🎯 Retomar" en el header del thread (disponible siempre)
- [ ] Click abre modal con:
  - Acciones predefinidas relevantes al contexto (lista de chips):
    - "📊 Enviar caso de exito"
    - "❓ Preguntar status"
    - "🎁 Ofrecer descuento"
    - "📅 Ofrecer agendar cita"
    - "💡 Compartir contenido relevante"
  - Campo de texto libre: "O escribe tu propio objetivo..."
  - Boton: "Ejecutar"
- [ ] Al ejecutar:
  - API call: `POST /conversations/{leadId}/nudge` con `instruction`
  - El AI genera y envia un mensaje al lead incorporando la instruccion
  - El mensaje aparece en el thread como burbuja violeta del AI
  - Evento del sistema: "🎯 [Owner] activo nudge: [objetivo resumido]"
- [ ] El nudge funciona independientemente del `handler_mode`

**Decision de implementacion:** El endpoint `nudge` crea un mensaje sintetico de sistema, invoca el grafo LangGraph con la instruccion como input, y envia la respuesta generada por el channel adapter. Es como simular que el lead escribio algo, pero en realidad es el owner disparando al AI.

---

#### US-2.5: Reanudar el AI (RESUME)

**Como** owner, **quiero** devolver el control al Sales Agent, **para** que retome la conversacion de forma autonoma.

**Criterios de aceptacion:**
- [ ] Boton "▶️ Reanudar AI" visible cuando `handler_mode=human`
- [ ] Click abre opciones:
  - "Reanudar sin instrucciones" — el AI retoma donde quedo
  - "Reanudar con objetivo" — abre campo de texto para dar una directriz
- [ ] Al confirmar:
  - API call: `POST /conversations/{leadId}/resume` con `mode=ai` y opcionalmente `objective`
  - `handler_mode` cambia a `ai`
  - `paused_at` se limpia
  - Si hay objetivo, se almacena en `resume_objective`
  - Header vuelve a "🤖 AI Activo"
  - Badge en lista vuelve a "🤖 AI"
  - Evento del sistema: "▶️ [Owner] devolvio control al AI" (+ "con objetivo: [texto]" si aplica)
- [ ] El AI responde al proximo mensaje del lead (o inmediatamente si hay `resume_objective` via nudge)

---

### EPIC 3: Pipeline (Vista Kanban)

---

#### US-3.1: Ver pipeline como Kanban

**Como** owner, **quiero** ver todas mis conversaciones organizadas por etapa del pipeline en un tablero Kanban, **para** tener vision de alto nivel de mi embudo de ventas.

**Criterios de aceptacion:**
- [ ] Vista accesible via tab "Pipeline" en el layout del Studio
- [ ] 6 columnas (simplificacion de los LeadStatus del CRM):
  | Columna (UI) | LeadStatus (CRM source of truth) | Color |
  |---|---|---|
  | Nuevo | `awareness` | Indigo |
  | Calificando | `qualified`, `disqualified` | Violeta |
  | Negociando | `negotiation`, `objection_handling` | Amarillo |
  | Cita Agendada | `call_booked` | Naranja |
  | Cerrado ✅ | `enrolled`, `downsell_accepted` | Verde |
  | Perdido | `disqualified` (con flag loss_reason) | Rojo |
- [ ] Cada columna muestra: titulo, color de acento, contador de cards
- [ ] Scroll horizontal si las columnas exceden el viewport
- [ ] El mapping de LeadStatus a columna es una funcion pura (sin estado adicional en DB)

**Decision de implementacion:** `disqualified` puede aparecer en "Calificando" o "Perdido" dependiendo del contexto. Si el lead fue descalificado durante calificacion (fit_score < umbral) va a "Perdido". Si el lead esta en proceso de calificacion va a "Calificando". El discriminante es: si `temperature=COLD` y `intent_score < 20` → Perdido. De lo contrario → Calificando.

---

#### US-3.2: Cards del Pipeline

**Como** owner, **quiero** que cada card en el Kanban me de informacion suficiente para decidir si necesita mi atencion, **para** no tener que abrir cada conversacion.

**Criterios de aceptacion:**
- [ ] Cada card muestra:
  - Nombre del lead
  - Icono del canal (emoji o icono)
  - Preview del ultimo mensaje (2 lineas max)
  - Badge de temperatura (borde izquierdo color)
  - Score numerico (coloreado: >70 verde, 40-70 amarillo, <40 gris)
  - Badge handler (🤖 AI / 👤 Tu / ⚠️ Escalada)
  - Tiempo desde ultima actividad ("3m", "2h", "1d")
  - Producto de interes (chip violeta)
  - Si hay cita: fecha y hora de la cita (texto naranja)
  - Si esta cerrado: monto de la venta (texto verde)
- [ ] Cards escaladas tienen borde rojo y sombra sutil
- [ ] Cards hot tienen borde-left rojo
- [ ] Click en una card navega a `/sales/studio/inbox?lead={leadId}` (abre en Inbox con esa conversacion)
- [ ] Cards son draggables entre columnas (actualiza `lead_status` via API)

**Decision de implementacion:** El drag & drop usa `@dnd-kit/core` (ya es dependencia de Shadcn). Al soltar en otra columna, se llama `PUT /api/v1/crm/pipeline/{profileId}/stage` con el nuevo status correspondiente a la columna destino.

---

#### US-3.3: Filtrar Pipeline

**Como** owner, **quiero** filtrar el pipeline por canal, temperatura o producto, **para** enfocar la vista en un segmento especifico.

**Criterios de aceptacion:**
- [ ] Barra de filtros arriba del Kanban: canal | temperatura | producto
- [ ] Los filtros aplican a todas las columnas simultaneamente
- [ ] Cards que no coinciden se ocultan con animacion
- [ ] La URL refleja filtros: `?stage=negociando&filter=hot`
- [ ] "Limpiar filtros" restaura vista completa

---

### EPIC 4: Conversaciones Congeladas

---

#### US-4.1: Ver lista de conversaciones congeladas

**Como** owner, **quiero** ver todas las conversaciones que se estancaron (sin actividad prolongada), **para** decidir cuales reactivar y cuales descartar.

**Criterios de aceptacion:**
- [ ] Vista accesible via tab "Congeladas" con badge de conteo (rojo si >0)
- [ ] Stats arriba: 3 chips mostrando conteo de "Urgentes (Hot + 48h)", "Recuperables", "Probablemente perdidas"
- [ ] Una conversacion se clasifica como congelada si:
  - `is_active=true` AND ultima actividad > 72h (configurable)
  - O: `handler_mode=human` AND ultima actividad > 24h (escalacion sin respuesta)
- [ ] Cada card muestra:
  - Avatar + nombre + canal + etapa + score + temperatura
  - Ultimo mensaje del lead (italico, gris)
  - Tiempo congelada ("hace 3 dias")
  - Diagnostico AI (ver US-4.2)
  - Quick actions (ver US-4.3)
- [ ] Cards ordenadas por urgencia: Hot primero, luego por tiempo congelada ascendente
- [ ] Cards urgentes (Hot + >48h) tienen borde rojo
- [ ] Cards recuperables tienen borde amarillo
- [ ] Cards probablemente perdidas tienen borde gris

---

#### US-4.2: Diagnostico AI de conversacion congelada

**Como** owner, **quiero** que el AI me diga por que se congelo una conversacion y que sugiere hacer, **para** tomar una decision informada sin tener que leer todo el historial.

**Criterios de aceptacion:**
- [ ] Cada card de congelada muestra seccion "Diagnostico AI":
  - **Razon probable**: texto en amarillo (ej: "Necesita validacion de socio. Riesgo de perder momentum.")
  - **Sugerencia**: texto en gris (ej: "Enviar caso de exito similar + preguntar si necesita info para su socio")
- [ ] El diagnostico se genera bajo demanda la primera vez (POST `/conversations/{leadId}/diagnose`)
- [ ] Una vez generado, se cachea en `frozen_diagnosis` (JSONB en checkpoint)
- [ ] Si el diagnostico tiene mas de 7 dias, se ofrece regenerarlo
- [ ] El diagnostico usa el LLM con:
  - Ultimos 20 mensajes de la conversacion
  - Perfil del lead (profile_data)
  - Estado del checkpoint (current_stage, lead_score, objection_history)
  - Prompt: "Analiza por que esta conversacion se estanco y sugiere estrategia de re-engagement"

**Decision de implementacion:** Usar `ModelRole.FAST` (Haiku) para los diagnosticos — es rapido y barato. El resultado es un JSON estructurado: `{ reason: string, suggestion: string, confidence: "high"|"medium"|"low", recommended_actions: string[] }`.

---

#### US-4.3: Acciones rapidas de reactivacion

**Como** owner, **quiero** reactivar una conversacion congelada con un click usando acciones predefinidas, **para** no tener que pensar en que escribir cada vez.

**Criterios de aceptacion:**
- [ ] Debajo del diagnostico, fila de chips de acciones rapidas:
  - "📊 Enviar caso de exito"
  - "❓ Preguntar status"
  - "🎁 Ofrecer descuento"
  - "👋 Follow-up ligero"
  - "💡 Compartir contenido"
  - "📝 Objetivo custom..."
- [ ] Click en accion predefinida abre confirmacion: "Reactivar con: [accion]. El AI enviara un mensaje al lead."
- [ ] Click en "📝 Objetivo custom..." expande un campo de texto inline
- [ ] Boton "🎯 Reactivar" ejecuta la accion:
  - API call: `POST /conversations/{leadId}/reactivate` con `objective` y opcionalmente `initial_message`
  - Se limpia `frozen_at`, `frozen_reason`
  - Se setea `resume_objective` con la accion
  - El AI genera y envia un mensaje al lead
  - La card desaparece de la lista de congeladas
  - Aparece en Inbox como conversacion activa
- [ ] Boton "👁️ Ver conv." navega a `/sales/studio/inbox?lead={leadId}` para leer el historial completo antes de decidir
- [ ] Boton "✕ Descartar" marca como perdida (mueve a estado `disqualified` con `loss_reason=frozen_discard`)

---

#### US-4.4: Reactivacion en bulk

**Como** owner, **quiero** reactivar multiples conversaciones congeladas con un patron comun, **para** no tener que hacerlo una por una.

**Criterios de aceptacion:**
- [ ] Checkbox en cada card + checkbox "Seleccionar todas las recuperables" en barra inferior
- [ ] Barra de acciones bulk aparece al seleccionar: "🎯 Reactivar seleccionadas (patron: [dropdown])" | "Descartar seleccionadas"
- [ ] El patron bulk es uno de los quick actions (follow-up ligero, ofrecer descuento, etc.)
- [ ] Al ejecutar, se llama `reactivate` para cada lead seleccionado en paralelo
- [ ] Progress indicator: "Reactivando 4/7..."
- [ ] Cards reactivadas desaparecen de la lista con animacion

---

### EPIC 5: Command Center (KPI Bar)

---

#### US-5.1: Ver metricas clave en tiempo real

**Como** owner, **quiero** ver KPIs criticos en la barra superior del Studio, **para** saber como va el negocio de un vistazo.

**Criterios de aceptacion:**
- [ ] Barra superior (dentro del layout del Studio, debajo de las tabs) muestra chips:
  - **Escaladas**: Conteo con dot rojo pulsante (animacion CSS). Click filtra la lista.
  - **Activas**: Total de conversaciones activas
  - **🔴 Hot**: Conteo de leads hot
  - **Cerradas hoy**: Con color verde
  - **Revenue hoy**: Formato `$X,XXX`
  - **⌘K**: Hint de atajo de busqueda
- [ ] Los KPIs se actualizan via WebSocket (no polling)
- [ ] Endpoint: `GET /api/v1/closer-studio/kpis?period=today`
- [ ] Cada chip es clickeable: filtra la vista actual (inbox o pipeline) al criterio correspondiente

---

### EPIC 6: Real-Time (WebSocket)

---

#### US-6.1: Mensajes en tiempo real

**Como** owner, **quiero** que los nuevos mensajes aparezcan instantaneamente sin recargar, **para** tener visibilidad en tiempo real de mis conversaciones.

**Criterios de aceptacion:**
- [ ] WebSocket connection al cargar el Studio: `ws://host/ws/closer-studio?token={clerkJWT}`
- [ ] Autenticacion via JWT en el query param del handshake
- [ ] Eventos soportados:
  | Evento | Accion en UI |
  |---|---|
  | `new_message` | Append mensaje al thread abierto + actualizar preview en lista + incrementar unread |
  | `ai_response` | Append respuesta AI al thread + actualizar preview en lista |
  | `status_change` | Actualizar badge handler en lista + header del thread |
  | `new_conversation` | Agregar item nuevo al tope de la lista |
  | `escalation` | Toast notification + resaltar conversacion + sonido |
  | `frozen` | Incrementar badge del tab Congeladas |
  | `delivery_confirm` | Checkmark en mensaje enviado por humano |
- [ ] Si el WS se desconecta, reconexion automatica con backoff exponencial (1s, 2s, 4s, max 30s)
- [ ] Indicador visual de estado WS: dot verde (conectado) / rojo (desconectado) en la barra superior
- [ ] Fallback: si WS falla, polling cada 30s para la lista de conversaciones

**Decision de implementacion:** Backend usa dict in-process `active_connections[tenant_id]` para dev. Para produccion (multi-worker), se agrega Redis pub/sub como transport. El WS endpoint vive en `backend/src/modules/sales_agent/api/ws.py`.

---

#### US-6.2: Notificaciones de escalacion

**Como** owner, **quiero** recibir una notificacion prominente cuando el AI escale una conversacion, **para** atenderla antes de perder al lead.

**Criterios de aceptacion:**
- [ ] Cuando llega evento `escalation` via WS:
  - Toast notification (Sonner): "⚠️ Escalacion: [nombre] necesita atencion humana"
  - Sonido de alerta (configurable, off por defecto)
  - Badge en el tab "Inbox" del sidebar principal se incrementa
  - La conversacion escalada sube al tope de la lista con borde rojo
  - El chip "Escaladas" en la KPI bar se actualiza
- [ ] Si el owner no esta en el Studio, la notificacion aparece como browser notification (si tiene permisos)

---

### EPIC 7: URLs Deep-Linked (para Copilot)

---

#### US-7.1: Cada vista y accion tiene URL unica

**Como** sistema (Copilot), **quiero** que cada estado del Studio tenga una URL unica, **para** poder navegar al owner directamente a la accion correcta.

**Criterios de aceptacion:**
- [ ] Esquema de URLs:
  ```
  /[tenantId]/sales/studio/inbox                          -- Inbox sin seleccion
  /[tenantId]/sales/studio/inbox?lead={uuid}              -- Inbox con conversacion abierta
  /[tenantId]/sales/studio/inbox?lead={uuid}&tab=info     -- Con sidebar en tab especifico
  /[tenantId]/sales/studio/inbox?filter=hot               -- Inbox filtrado
  /[tenantId]/sales/studio/inbox?filter=hot&handler=ai    -- Filtro combinado
  /[tenantId]/sales/studio/pipeline                       -- Pipeline Kanban
  /[tenantId]/sales/studio/pipeline?stage=negociando      -- Pipeline con columna resaltada
  /[tenantId]/sales/studio/frozen                         -- Congeladas
  /[tenantId]/sales/studio/frozen?lead={uuid}             -- Con card expandida
  ```
- [ ] Todos los query params se sincronizan bidirecionalmente con el Zustand store via `useSearchParams()`
- [ ] Navegar a una URL con params pre-llena el estado correcto (ej: abrir `?lead=X` selecciona esa conversacion)
- [ ] Cambiar filtros/seleccion actualiza la URL (sin page reload)
- [ ] Las URLs son compartibles (copiar/pegar abre el mismo estado)
- [ ] Registrar rutas en `navigation_map.py` del Copilot para que el asistente pueda navegar

---

### EPIC 8: Keyboard Shortcuts

---

#### US-8.1: Navegacion rapida por teclado

**Como** owner power-user, **quiero** atajos de teclado para las acciones mas frecuentes, **para** operar el Studio sin tocar el mouse.

**Criterios de aceptacion:**
- [ ] `⌘K` / `Ctrl+K`: Abrir busqueda global
- [ ] `↑` / `↓`: Navegar entre conversaciones en la lista (cuando lista tiene foco)
- [ ] `Enter`: Abrir conversacion seleccionada
- [ ] `S`: Toggle STOP/RESUME AI en conversacion activa
- [ ] `E`: Enfocar input de mensaje (modo directo)
- [ ] `I`: Enfocar input de instruccion (modo instruccion)
- [ ] `Esc`: Cerrar modal / deseleccionar conversacion
- [ ] `1`-`5`: Cambiar filtro rapido (1=Todas, 2=Hot, 3=Warm, 4=Cold, 5=Escaladas)
- [ ] Los shortcuts solo aplican cuando el Studio tiene foco (no interfieren con inputs de texto)
- [ ] Hint visual de shortcuts disponibles (tooltip o `?` para mostrar lista)

---

## 6. Modelo de Datos — Cambios Requeridos

### 6.1 Nuevas columnas en `agent_state_checkpoints`

```sql
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS handler_mode VARCHAR(20) DEFAULT 'ai';
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS paused_at TIMESTAMP NULL;
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS paused_by UUID NULL;
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS resume_objective TEXT NULL;
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS frozen_reason VARCHAR(100) NULL;
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS frozen_at TIMESTAMP NULL;
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS frozen_diagnosis JSONB NULL;
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS last_human_message_at TIMESTAMP NULL;
ALTER TABLE agent_state_checkpoints ADD COLUMN IF NOT EXISTS unread_count INTEGER DEFAULT 0;
CREATE INDEX IF NOT EXISTS ix_checkpoint_handler_mode ON agent_state_checkpoints(tenant_id, handler_mode) WHERE is_active = true AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_checkpoint_frozen ON agent_state_checkpoints(tenant_id, frozen_at) WHERE frozen_at IS NOT NULL AND is_active = true;
```

### 6.2 Nueva columna en `messages`

```sql
ALTER TABLE messages ADD COLUMN IF NOT EXISTS sender_source VARCHAR(20) DEFAULT 'auto';
-- Valores: 'auto' (AI), 'human_direct', 'human_instruction', 'system'
```

### 6.3 No se crean tablas nuevas

El pipeline simplificado es una vista computada sobre `LeadStatus`. Las conversaciones congeladas se detectan por `frozen_at IS NOT NULL`.

---

## 7. API Endpoints

Prefijo: `/api/v1/closer-studio`
Archivo: `backend/src/modules/sales_agent/api/closer_studio.py`

| Metodo | Ruta | Descripcion | Response Model |
|---|---|---|---|
| GET | `/conversations` | Lista filtrable de conversaciones | `ConversationListResponse` |
| GET | `/conversations/{lead_id}` | Detalle con mensajes + metadata | `ConversationDetailResponse` |
| POST | `/conversations/{lead_id}/stop` | Pausar AI | `ActionResponse` |
| POST | `/conversations/{lead_id}/resume` | Reanudar AI (con/sin objetivo) | `ActionResponse` |
| POST | `/conversations/{lead_id}/messages` | Enviar mensaje directo o instruccion | `MessageResponse` |
| POST | `/conversations/{lead_id}/nudge` | AI envia mensaje proactivo | `NudgeResponse` |
| POST | `/conversations/{lead_id}/reactivate` | Reactivar conversacion congelada | `ActionResponse` |
| POST | `/conversations/{lead_id}/diagnose` | Generar diagnostico AI | `DiagnosisResponse` |
| GET | `/frozen` | Lista de conversaciones congeladas | `FrozenListResponse` |
| GET | `/kpis` | Metricas resumen del periodo | `KPISummaryResponse` |
| WS | `/ws/closer-studio` | WebSocket para tiempo real | N/A |

Todos los endpoints filtran por `tenant_id` (del header `X-Tenant-ID`).
Todos declaran `response_model=` con Pydantic model (cumplimiento PII sanitisation).

---

## 8. WebSocket — Diseno

### 8.1 Endpoint

```python
@router.websocket("/ws/closer-studio")
async def closer_studio_ws(websocket: WebSocket):
    # Auth: Extract Clerk JWT from ?token= query param
    # Subscribe: Add to active_connections[tenant_id]
    # Keep alive: Ping/pong cada 30s
    # On disconnect: Remove from active_connections
```

### 8.2 Eventos

```typescript
type WSEvent = {
  type: "new_message" | "ai_response" | "status_change" | "new_conversation" | "escalation" | "frozen" | "delivery_confirm";
  lead_id: string;
  payload: Record<string, unknown>; // Datos especificos del evento
  timestamp: string; // ISO 8601
};
```

### 8.3 Emision

Funcion `emit_ws_event(tenant_id, event_type, payload)` llamada desde:
- `ChatOrchestrator.process_chat_flow()` — despues de recibir mensaje del lead
- `ChatOrchestrator` — despues de que el AI responde
- `tool_escalate_to_human` — cuando el AI escala
- Endpoints de `closer_studio.py` — cuando el owner hace acciones

### 8.4 Escalabilidad

| Etapa | Transporte | Workers |
|---|---|---|
| Dev | Dict in-process | 1 worker |
| Staging | Redis pub/sub | N workers |
| Prod | Redis pub/sub | N workers |

---

## 9. Integracion con ChatOrchestrator

### 9.1 Flujo modificado de `process_chat_flow()`

```
Mensaje llega del lead
  ↓
Cargar checkpoint activo
  ↓
¿handler_mode == 'human'?
  SÍ → Guardar mensaje en DB
     → Incrementar unread_count
     → Emitir WS "new_message"
     → RETURN (no invocar AI)
  NO ↓
¿handler_mode == 'hybrid'?
  SÍ → Emitir WS "new_message" (para awareness)
     → Continuar con AI
  NO ↓
¿Hay resume_objective?
  SÍ → Inyectar como mensaje de sistema en AgentState
     → Limpiar resume_objective
  NO ↓
Invocar LangGraph
  ↓
AI genera respuesta
  ↓
¿handler_mode sigue siendo != 'human'? (re-check por race condition)
  SÍ → Enviar respuesta por channel adapter
     → Emitir WS "ai_response"
  NO → Guardar como draft, no enviar
```

### 9.2 Archivos a modificar

| Archivo | Cambio |
|---|---|
| `backend/src/modules/sales_agent/application/orchestrator/chat.py` | Check handler_mode, inject resume_objective, emit WS events |
| `backend/src/modules/sales_agent/infrastructure/models/agent_state_checkpoint_model.py` | Nuevas columnas |
| `backend/src/modules/sales_agent/infrastructure/models/message_model.py` | Nueva columna sender_source |
| `backend/src/modules/sales_agent/application/agents/sales/prompts/supervisor_routing.j2` | Reconocer `[INSTRUCCION DEL OPERADOR]` |
| `backend/src/main.py` | Montar nuevo router + WS endpoint |

---

## 10. Frontend — Estructura de Archivos

```
frontend/src/features/closer-studio/
  api/
    index.ts                    -- fetchConversations, fetchConversationDetail, stopAI, resumeAI, sendMessage, nudge, reactivate, diagnose, fetchKPIs, fetchFrozen
  components/
    closer-layout.tsx           -- Shared layout: tabs + KPI bar
    inbox/
      conversation-list.tsx     -- Panel izquierdo
      conversation-item.tsx     -- Item individual de la lista
      conversation-thread.tsx   -- Panel central con mensajes
      contact-sidebar.tsx       -- Panel derecho
      message-input.tsx         -- Input con toggle directo/instruccion
      message-bubble.tsx        -- Burbuja de mensaje
      system-event.tsx          -- Banner de evento del sistema
      thread-header.tsx         -- Header con nombre + acciones
    pipeline/
      pipeline-board.tsx        -- Contenedor horizontal de columnas
      pipeline-column.tsx       -- Columna individual
      pipeline-card.tsx         -- Card de lead
    frozen/
      frozen-list.tsx           -- Lista de conversaciones congeladas
      frozen-card.tsx           -- Card individual
      frozen-diagnosis.tsx      -- Seccion de diagnostico AI
      quick-actions.tsx         -- Chips de acciones rapidas
      custom-objective.tsx      -- Input de objetivo personalizado
    shared/
      channel-badge.tsx         -- Badge de canal (IG/WA/TG/Web)
      handler-badge.tsx         -- Badge de handler (AI/Humano/Escalada)
      temperature-dot.tsx       -- Dot de temperatura (rojo/amarillo/azul)
      stage-chip.tsx            -- Chip de etapa del pipeline
      score-ring.tsx            -- (reusar de features/sales/components/atoms/ScoreRing.tsx)
  hooks/
    use-conversations.ts        -- useQuery para lista
    use-conversation-detail.ts  -- useQuery para detalle
    use-conversation-actions.ts -- useMutation para stop/resume/reactivate
    use-send-message.ts         -- useMutation para enviar mensaje/instruccion/nudge
    use-closer-ws.ts            -- WebSocket hook con reconexion
    use-kpis.ts                 -- useQuery para KPIs
    use-frozen.ts               -- useQuery para congeladas
    use-diagnose.ts             -- useMutation para diagnostico AI
  store/
    closer-store.ts             -- Zustand: selectedLeadId, filters, inputMode, unreadByLead, wsConnected, sidebarOpen
  types/
    index.ts                    -- Interfaces TS: Conversation, ConversationDetail, Message, Lead, KPIs, FrozenConversation, Diagnosis, PipelineStage
```

---

## 11. Componentes Reutilizables del Codebase Existente

| Componente | Ubicacion actual | Uso en Closer Studio |
|---|---|---|
| `ScoreRing` | `features/sales/components/atoms/ScoreRing.tsx` | Sidebar: fit/intent score |
| `TemperatureBadge` | `features/sales/components/atoms/TemperatureBadge.tsx` | Lista + cards |
| `LeadAvatar` | `features/sales/components/atoms/LeadAvatar.tsx` | Lista + sidebar |
| Channel icons | `features/connections/config/` | Badges de canal |
| `ScrollArea` | Shadcn UI | Lista de conversaciones + thread |
| `Tabs` | Shadcn UI | Tab navigation del layout |
| `Badge` | Shadcn UI | Contadores + estados |
| `Avatar` | Shadcn UI | Avatares de leads |
| `Button` | Shadcn UI | Todas las acciones |
| `Card` | Shadcn UI | Pipeline cards + frozen cards |
| `Input` / `Textarea` | Shadcn UI | Search + message input |
| `Sheet` | Shadcn UI | Modales de confirmacion |
| `Sonner` (toast) | Shadcn UI | Notificaciones de escalacion |

---

## 12. Deteccion Automatica de Conversaciones Congeladas

**Tarea programada** (ARQ worker, cada 4 horas):

```python
async def detect_frozen_conversations(ctx):
    """
    Para cada tenant:
    1. Buscar checkpoints activos donde ultimo mensaje > 72h
    2. Buscar checkpoints con handler_mode='human' y ultima actividad > 24h
    3. Setear frozen_at, frozen_reason
    4. Emitir WS event 'frozen'
    """
```

**Razones de congelamiento:**
- `inactivity_72h` — sin actividad de ningun lado > 72h
- `escalation_timeout` — escalado a humano pero sin respuesta > 24h
- `lead_ghosted` — lead no respondio a ultimos 2 mensajes del AI

---

## 13. Channel Resolver (Envio Bidireccional)

Nuevo servicio: `backend/src/modules/sales_agent/application/services/channel_resolver.py`

Resuelve el adapter de canal correcto + user_id para enviar mensajes salientes al lead:

1. Determina el canal del ultimo mensaje del lead (campo `channel` en `messages`)
2. Busca `ChannelConnectionModel` activa para ese canal + tenant
3. Instancia el adapter correspondiente:
   - `telegram` → `TelegramChannel(token=creds["token"])`
   - `whatsapp` → `WhatsAppFactory.create(tenant_id, ...)`
   - `instagram` → `InstagramChannel(config, creds)`
4. Resuelve `channel_user_id` del lead: `telegram_id`, `whatsapp_id`, o `instagram_id`

---

## 14. Handler Mode — Maquina de Estados

```
         POST /stop            POST /resume(mode=ai)
  [ai] ──────────→ [human] ──────────────────────→ [ai]
   │                  │                               ↑
   │                  │  POST /resume(mode=hybrid)    │
   │                  ↓                               │
   │              [hybrid] ───────────────────────────┘
   │                  │
   │             (inactivity 72h+ detectada por scheduled task)
   │                  ↓
   └──────────→ [frozen]
                      │
                 POST /reactivate
                      ↓
                    [ai]
```

Transiciones validas:
- `ai` → `human` (via STOP)
- `ai` → `frozen` (via scheduled task)
- `human` → `ai` (via RESUME)
- `human` → `hybrid` (via RESUME con mode=hybrid)
- `human` → `frozen` (via scheduled task si no hay actividad)
- `hybrid` → `ai` (via RESUME)
- `hybrid` → `human` (via STOP)
- `frozen` → `ai` (via REACTIVATE)

---

## 15. Decisiones de Implementacion Pendientes

| # | Decision | Opciones | Recomendacion |
|---|---|---|---|
| D1 | Sonido de escalacion | Browser Audio API vs libreria | Browser Audio API (nativo, sin deps) |
| D2 | Drag & drop en Pipeline | `@dnd-kit/core` vs `react-beautiful-dnd` | `@dnd-kit` (mantenido, accesible, ya compatible con Shadcn) |
| D3 | Diagnostico AI — modelo | Haiku (rapido/barato) vs Sonnet (mejor calidad) | Haiku para v1, upgrade si la calidad no es suficiente |
| D4 | Notas del owner — storage | Campo en LeadModel vs tabla separada | Campo `owner_notes` en LeadModel (simple, suficiente para v1) |
| D5 | WS reconexion — estrategia | Manual vs libreria | Manual con exponential backoff (evitar deps extra) |
| D6 | Virtual scroll en lista | `@tanstack/react-virtual` vs scroll nativo | `@tanstack/react-virtual` (ya es dep de TanStack Query) |
| D7 | Pipeline drag-drop — actualizacion | Optimistic update vs server-first | Optimistic con rollback on error (mejor UX) |
| D8 | Thread scroll — direccion | Bottom-up (como chat) vs top-down | Bottom-up: nuevos mensajes abajo, scroll up para historial |

---

## 16. Verificacion y Testing

### Backend
```bash
# Migration
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"

# Lint
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache"

# Tests
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"

# Test WS manually
python -c "import asyncio, websockets; asyncio.run(websockets.connect('ws://localhost:8000/ws/closer-studio?token=...'))"
```

### Frontend
```bash
# TypeScript
docker exec -t visionarias_client_dev npx tsc --noEmit

# Lint
docker exec -t visionarias_client_dev npx next lint

# Tests
docker exec -t visionarias_client_dev npm run test
```

### E2E Manual
1. Abrir Closer Studio → verificar lista de conversaciones cargada
2. Click en conversacion → thread muestra mensajes
3. Click STOP → verificar que el AI no responde a siguiente mensaje del lead
4. Enviar mensaje directo → verificar que llega al canal del lead
5. Enviar instruccion → verificar que el AI la incorpora en proximo mensaje
6. Click Reanudar → verificar que AI retoma
7. Abrir Pipeline → verificar columnas con cards correctas
8. Drag card → verificar que status se actualiza
9. Abrir Congeladas → verificar diagnostico AI
10. Reactivar → verificar que se envia mensaje y desaparece de congeladas
11. Verificar WebSocket: enviar mensaje desde otro canal y ver que aparece en real-time
12. Verificar URLs: copiar URL con `?lead=X`, pegar en otra tab, verificar mismo estado
