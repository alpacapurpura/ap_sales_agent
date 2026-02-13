# Manual Funcional y Guía de Uso del Sistema Visionarias AI

Este documento sirve como **mapa de navegación y manual de usuario** para el sistema Visionarias AI. Aquí encontrarás qué hace cada módulo, para qué sirve a nivel de negocio y cómo utilizarlo paso a paso.

---

## 🔐 1. Acceso y Seguridad
*El punto de entrada para gestionar tu fuerza de ventas digital.*

### 📍 `/sign-in` (Iniciar Sesión)
*   **Para qué sirve:** Para que tú y tu equipo accedan de forma segura al panel de control.
*   **Funcionalidad:**
    *   Ingreso con correo y contraseña.
    *   Soporte para cuentas corporativas (Google/Microsoft).
*   **Resultado:** Te lleva directamente al **Dashboard Principal**.

### 📍 `/sign-up` (Registro de Nueva Empresa)
*   **Para qué sirve:** Para dar de alta una nueva empresa (Tenant) en la plataforma.
*   **Funcionalidad:**
    *   Creación de cuenta maestra.
    *   Configuración inicial del nombre de la organización.
*   **Resultado:** Crea tu espacio de trabajo privado y aislado de otros clientes.

---

## 🏠 2. Dashboard Principal
**Ruta:** `📍 /`
*   **Misión:** Tu centro de comando. Te dice "cómo va el negocio" de un vistazo.
*   **Para qué sirve:** Para monitorear la salud de tu agente de ventas y acceder rápidamente a las tareas más importantes.

*   👁️ **Métricas Clave (KPIs):**
    *   **Estado del Agente:** Semáforo que indica si tu IA está activa y respondiendo.
    *   **Cerebro (Vectores):** Cuántos fragmentos de información tiene tu IA listos para usar.
    *   **Biblioteca (Documentos):** Cuántos archivos PDF/Docs ha procesado y entendido.
*   🔘 **Accesos Directos:**
    *   Botones rápidos para ir a configurar ofertas, auditar conversaciones o entrenar a la IA.

---

## 💎 3. Offer Studio (Fábrica de Ofertas)
**Ruta:** `📍 /offer-studio`
*   **Misión:** Definir **QUÉ** vende tu IA.
*   **Para qué sirve:** Aquí configuras tus productos High-Ticket. La IA usará esta información para vender. Si no está aquí, la IA no lo vende.

### 📍 Lista de Ofertas
*   **Vista:** Tabla con todos tus productos activos y borradores.
*   **Acción:** Crear una nueva oferta desde cero.

### 📍 Editor de Oferta (Detalle)
Una vez dentro de una oferta, tienes 4 áreas clave para "enseñarle" a la IA cómo venderla:

#### 1. Resumen y Promesa (`/offer-studio/offer/[id]`)
*   **Negocio:** Define el precio y la "Promesa de Transformación" (¿Qué logra el cliente?).
*   **Uso:** Escribe la promesa en formato "Del Infierno al Cielo" (ej: "Pasa de no tener tiempo a automatizar todo").
*   **Estrategia:** Le dices a la IA si es una venta "Evergreen" (siempre abierta) o "Lanzamiento" (con fecha límite).

#### 2. Avatar / Cliente Ideal (`.../avatar`)
*   **Negocio:** Define **A QUIÉN** le vendemos.
*   **Uso:** Describes los dolores, deseos y miedos de tu cliente ideal.
*   **Anti-Avatar:** Muy importante: defines a quién **NO** queremos venderle (para que la IA los filtre).

#### 3. Objeciones (`.../objections`)
*   **Negocio:** Prepara a la IA para la "guerra".
*   **Uso:** Escribes las excusas típicas ("Es muy caro", "No tengo tiempo") y le das a la IA los mejores scripts para rebatirlas.
*   **Trigger:** La frase que detona la defensa.

#### 4. Conocimiento Específico (`.../knowledge`)
*   **Negocio:** Material de apoyo exclusivo para este producto.
*   **Uso:** Subes PDFs o textos que solo aplican a esta oferta (ej: Temario del curso, Garantía específica).

---

## 🧬 4. Brand Settings (Identidad de Marca)
**Ruta:** `📍 /brand-settings`
*   **Misión:** Definir **QUIÉN** vende (La personalidad de la IA).
*   **Para qué sirve:** Para que la IA no suene como un robot genérico, sino como TÚ o tu MARCA.

### 🏢 Pestaña: Global
*   **Información Corporativa:** Quién es la empresa, misión y visión.
*   **Datos de Contacto:** Teléfonos, correos y direcciones que la IA puede dar si se los piden.

### 🛡️ Pestaña: Autoridad
*   **Key Figures (Equipo):** Quiénes son los expertos detrás de la marca (para generar confianza).
*   **Respaldo Institucional:** Premios, certificaciones o apariciones en prensa que validan tu autoridad.

### 🧠 Pestaña: Marca
*   **Avatares (Perfiles):** Gestión de los diferentes tipos de clientes (Buyer Personas) a nivel global.
*   **Personalidad IA (Clonación):**
    *   **Calibrador de Estilo:** Puedes subir chats antiguos o dar tu Instagram para que la IA analice tu tono (si usas emojis, si eres formal o informal) e imite tu voz.

---

## 📅 5. Ventas y Calendario (Sales)
**Ruta:** `📍 /sales`
*   **Misión:** Gestionar el **CIERRE**.
*   **Para qué sirve:** Controlar tu disponibilidad para llamadas de venta y ver quién ha agendado.

### ⚙️ Tipo de Cita
*   Configuras las reuniones que ofreces (ej: "Sesión de Estrategia - 45 min").
*   Defines si es por Google Meet, Zoom o teléfono.
*   **Resultado:** Genera un enlace público (tipo Calendly) para que tus clientes agenden solos.

### 🔗 Páginas Públicas (`/book/...`)
*   **Qué es:** La página que ven tus clientes al agendar.
*   **Experiencia:** El cliente ve tu logo, elige fecha/hora y recibe confirmación automática con el link de la reunión.

### 🕒 Disponibilidad
*   Marcas tu horario laboral. La IA nunca agendará fuera de estas horas.

### 📅 Reservas
*   Un tablero visual (tipo Google Calendar) donde ves todas tus citas agendadas por la IA.
*   Estados: Próximas, Canceladas, Pasadas.

---

## 🔌 6. Conexiones e Integraciones
**Ruta:** `📍 /connections`
*   **Misión:** Conectar la IA con el mundo exterior.
*   **Para qué sirve:** Centralizar todos los canales por donde entran clientes.

### 💬 Canales de Venta
*   **WhatsApp:** Conexión mediante código QR (como WhatsApp Web) para que la IA conteste tu celular.
*   **Telegram:** Conexión vía BotFather.
*   **Email:** Conexión con Gmail para redactar o responder correos.
*   **Otros (Próximamente):** Instagram, TikTok, Messenger.

### 🛠️ Herramientas de Cierre
*   **Calendario:** Conexión con Google Calendar (para que la IA no agende encima de tus eventos personales).

### 👨‍💻 Desarrolladores
*   **Webhooks:** Configuración avanzada para conectar con Zapier, Make o n8n.

---

## 🧠 7. Base de Conocimiento (Cerebro Global)
**Ruta:** `📍 /knowledge`
*   **Misión:** La biblioteca central de información de la empresa.
*   **Para qué sirve:** Todo lo que la IA necesita saber que NO es específico de una oferta (Políticas, Historia, FAQs generales).

*   **Documentos:** Subida de archivos (PDF, TXT, MD).
*   **Seguridad:** Filtros para evitar que la IA hable de la competencia o temas sensibles.
*   **Redacción de PII (Safety Layer):** El sistema detecta automáticamente datos sensibles (Tarjetas de crédito, DNI) y los encripta/elimina.
*   **Reglas de Negocio:** Horarios de atención del bot y límites de mensajes por usuario (para controlar costos).

---

## 🕵️ 8. Auditoría y Trazas
**Ruta:** `📍 /audit`
*   **Misión:** Supervisión y Control de Calidad.
*   **Para qué sirve:** Ver qué está hablando la IA en tiempo real y entender por qué dijo lo que dijo.

*   **Lista de Leads:** Ves a todas las personas que están hablando con el bot.
*   **Chat en Vivo:** Lees la conversación completa.
*   **Inspector de Cerebro (Trazas):**
    *   Si la IA comete un error, puedes ver su "pensamiento" interno (JSON) para entender qué razonamiento falló.
    *   Puedes ver qué variables de estado tiene guardadas sobre ese cliente (ej: ¿Ya sabe su nombre? ¿Ya sabe su presupuesto?).
*   **Botón de Pánico:** Opción para borrar el historial de un lead si es necesario reiniciar la conversación.

---

## ⚙️ 9. Configuración
**Ruta:** `📍 /settings`
*   **Misión:** Ajustes técnicos de la cuenta.
*   **Para qué sirve:** Gestión de claves y secretos.

*   **API Keys:** Donde pones tus claves de OpenAI, Anthropic o Gemini (el motor de la IA).
*   **Webhooks:** Datos técnicos para integradores.

---

## 🤖 10. Motor de Experiencia de Chat (IA Engine)
*El cerebro invisible que hace que la conversación se sienta humana.*

### 🧠 Smart Buffer (Agrupación de Mensajes)
*   **Problema:** Los usuarios humanos escriben en ráfagas ("Hola", "Tengo una duda", "¿Precio?").
*   **Solución:** El sistema espera unos segundos (debounce) para agrupar todos los mensajes fragmentados y procesarlos como una sola idea.

### 🎭 Humanización (Output Manager)
*   **Efecto:** Simulación de escritura ("Escribiendo...").
*   **Ritmo:** La IA no escupe bloques de texto instantáneos. Divide las respuestas largas en burbujas de chat naturales y simula el tiempo que tardaría un humano en escribirlas.

### 🚦 Router Semántico
*   **Función:** Un "portero" de alta velocidad que lee cada mensaje antes que el LLM principal.
*   **Uso:** Detecta intenciones críticas (como insultos, competidores o frases de compra inmediata) para desviar el flujo sin gastar recursos del modelo principal.

---

## 🔗 11. Páginas Públicas y Enlaces Mágicos
*Interfaces externas para tus clientes finales.*

### 📍 `/book/[empresa]/[evento]` (Página de Reserva)
*   **Caso de Uso:** Tu "Calendly" propio. Enlace público para compartir en redes o bio.
*   **Funcionalidad:** Selección de zona horaria, visualización de slots libres en tiempo real y confirmación automática.

### 📍 `/visit/[token]` (Magic Links)
*   **Caso de Uso:** Enlaces temporales o de un solo uso generados por el bot.
*   **Ejemplo:** "Aquí tienes un enlace exclusivo para retomar tu sesión de pago: [link]".
