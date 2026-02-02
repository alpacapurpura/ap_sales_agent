# Mapa de Funcionalidades y Navegación del Sistema (Sitemap)

Este documento detalla la **jerarquía completa de navegación** del sistema Visionarias AI. Úsalo para entender dónde encontrar cada funcionalidad y qué acciones específicas (clicks, inputs) se pueden realizar en cada pantalla.

---

## 🔐 1. Autenticación y Acceso
El punto de entrada seguro para usuarios y administradores.

### 📍 `/sign-in` (Login)
*   **Objetivo:** Autenticar al usuario vía Clerk.
*   📝 **Inputs:** `Email`, `Contraseña` (o Google/Microsoft OAuth).
*   🔘 **Acción Principal:** `[Sign In]` -> Redirige al **Dashboard (`/`)**.

### 📍 `/sign-up` (Registro)
*   **Objetivo:** Crear una nueva cuenta de Tenant.
*   📝 **Inputs:** `Email`, `Contraseña`, `Nombre de Empresa`.
*   🔘 **Acción Principal:** `[Create Account]` -> Inicia flujo de onboarding.

---

## 🏠 2. Dashboard Principal
**Ruta:** `📍 /`
**Objetivo:** Centro de comando y estado de salud del sistema.

*   👁️ **Tarjetas de Estado (Metrics):**
    *   `Estado de API`: (Online/Offline).
    *   `Vectores Indexados`: Contador total en Qdrant.
    *   `Documentos Procesados`: Contador total en Postgres.
*   🔘 **Navegación Rápida (Cards):**
    *   `[Ir a Offer Studio]` -> Navega a `/offer-studio`.
    *   `[Ver Auditoría]` -> Navega a `/audit`.
    *   `[Gestionar Conocimiento]` -> Navega a `/knowledge`.

---

## 🚀 3. Offer Studio (Gestión de Estrategia)
**Ruta:** `📍 /offer-studio`
**Objetivo:** Crear y configurar productos High-Ticket.

### 📍 `/offer-studio` (Listado)
*   👁️ **Lista de Ofertas:** Tabla con Nombre, Precio y Estado.
*   🔘 **Acción:** `[+ Nueva Oferta]` -> Crea borrador y redirige al Wizard.
*   🔘 **Acción:** `[Editar]` (en una fila) -> Navega a `/offer-studio/offer/[id]`.

### 📍 `/offer-studio/offer/[id]` (Editor de Oferta)
Este módulo tiene una **Sub-navegación Lateral** persistente.

#### 📑 Sub-menú: Resumen (General)
*   **Ruta:** `/offer-studio/offer/[id]`
*   📝 **Formulario (`OfferSummaryForm`):**
    *   Input: `Nombre de la Oferta`.
    *   Input: `Precio` (USD).
    *   Textarea: `Promesa de Transformación` (Heaven/Hell).
    *   Select: `Estrategia` (Evergreen / Lanzamiento).
*   🔘 **Acción:** `[Guardar Cambios]` -> Actualiza BD Postgres.

#### 📑 Sub-menú: Avatar (ICP)
*   **Ruta:** `/offer-studio/offer/[id]/avatar`
*   📝 **Formulario (`AvatarForm`):**
    *   Input: `Nombre del Avatar` (ej: "Dueños de Agencia").
    *   Textarea: `Descripción ICP` (Dolores, Deseos).
    *   Textarea: `Anti-Avatar` (A quién NO vender).
*   🔘 **Acción:** `[Asignar Avatar]` -> Vincula perfil al producto.

#### 📑 Sub-menú: Objeciones
*   **Ruta:** `/offer-studio/offer/[id]/objections`
*   👁️ **Lista de Objeciones:** Visualiza objeciones configuradas.
*   🔘 **Acción:** `[+ Agregar Objeción]` -> Abre formulario inline.
    *   📝 Input: `Trigger` (Frase detonante).
    *   📝 Input: `Estrategia` (Tipo de respuesta).
    *   📝 Textarea: `Script Sugerido`.

#### 📑 Sub-menú: Conocimiento Específico
*   **Ruta:** `/offer-studio/offer/[id]/knowledge`
*   📝 **Uploader (`AssetUploader`):**
    *   🔘 `[Seleccionar Archivo]` (PDF/TXT/MD).
    *   🔘 `[Subir]` -> Ingesta y vincula SOLO a esta oferta.

---

## 🧠 4. Base de Conocimiento (RAG Global)
**Ruta:** `📍 /knowledge`
**Objetivo:** Gestionar el cerebro de la IA y reglas de seguridad.
**Navegación Interna:** Pestañas superiores (`Tabs`).

### 📑 Tab: Documentos (`documents`)
*   👁️ **Tabla de Archivos:** Nombre, Tipo, Fecha, Estado Indexación.
*   🔘 **Acción:** `[+ Subir Nuevo]` -> Despliega área de carga.
    *   📝 Input: `Categoría` (Ventas, Legal, Producto).
    *   🔘 `[Upload]` -> Procesa Embeddings en Qdrant.

### 📑 Tab: Seguridad (`safety`)
*   👁️ **Selector de Nivel:**
    *   🔘 Radio: `Nivel Marca` (Global).
    *   🔘 Radio: `Nivel Producto` (Específico).
*   📝 **Configuración:**
    *   Checkboxes: `Filtrar Competencia`, `Bloquear Temas Sensibles`.

### 📑 Tab: Reglas (`rules`)
*   📝 **Reglas de Negocio:**
    *   Input: `Horario de Atención`.
    *   Input: `Máximo de Mensajes por Lead`.

---

## 🎨 5. Onboarding & Personalidad
**Ruta:** `📍 /onboarding`
**Objetivo:** Calibrar la "Voz" y estilo del agente.

### 📍 `/onboarding/style` (Calibrador)
*   📝 **Análisis Automático:**
    *   Input: `URL de Instagram/Web`.
    *   🔘 **Acción:** `[Analizar Estilo]` -> Scrapea y genera perfil.
*   📝 **Carga Manual:**
    *   Input: `Archivo de Chat Exportado` (.txt).
    *   🔘 **Acción:** `[Analizar Conversación]` -> Extrae frases y tono.
*   👁️ **Resultado (Style Profile):**
    *   Muestra: Tono detectado, Emojis sugeridos, Frases clave.

### 📍 `/avatars` (Gestión Global)
*   👁️ **Galería de Avatares:** Tarjetas con perfiles de clientes.
*   🔘 **Acción:** `[Crear Nuevo]` -> Va a formulario de creación.

---

## 🕵️ 6. Auditoría y Trazas
**Ruta:** `📍 /audit`
**Objetivo:** Observabilidad, debugging y revisión de conversaciones.
**Layout:** Master-Detail (Lista a la izquierda, Detalle a la derecha).

### 👈 Panel Izquierdo: Lista de Leads (`LeadList`)
*   👁️ **Lista Scrollable:** Leads con nombre, último mensaje y timestamp.
*   🔘 **Acción:** `Click en Lead` -> Carga la conversación en el panel derecho.

### 👉 Panel Derecho: Chat & Trazas (`ChatTimeline`)
*   👁️ **Timeline de Chat:** Mensajes del Usuario (Derecha) y Agente (Izquierda).
*   🔘 **Acción (Crítica):** `[🗑️ Icono Basura]` -> **Dialog:** "¿Borrar historial?" -> Elimina DB.
*   🔘 **Acción:** `[Ver Traza Técnica]` (en cada mensaje del agente).
    *   👁️ **Modal/Inspector:** Muestra JSON del razonamiento del nodo.
*   🔘 **Acción:** `[⚙️ Contexto]` -> **Sheet Lateral:**
    *   Muestra variables de estado (`state`), perfil de usuario y tags.

---

## ⚙️ 7. Configuración y Admin
**Ruta:** `📍 /settings`

### 📍 `/settings` (Tenant)
*   📝 **Integraciones:**
    *   Input: `Webhook URL` (Solo lectura, copiar).
    *   Input: `Webhook Secret` (Solo lectura, copiar).
    *   🔘 `[Regenerar Secreto]` -> Cambia la clave de seguridad.
*   📝 **API Keys:**
    *   Input: `OpenAI Key`.
    *   Input: `Gemini Key`.
    *   🔘 `[Guardar Keys]`.

### 📍 `/admin/tenants` (Super Admin)
*   👁️ **Tabla de Tenants:** Lista de todos los clientes suscritos.
*   🔘 **Acción:** `[Activar/Desactivar]` acceso.
