# Nueva Estrategia: Ecosistema de Ofertas Modular & Multi-Avatar

Entendido el problema. El modelo lineal "Wizard" y el "Avatar Singleton" no escalan para tu realidad de múltiples nichos y edición constante.

Aquí tienes la **Solución Alternativa** basada en una arquitectura modular y herencia de configuraciones (estilo Cloudflare/SaaS moderno).

## 1. Cambio Fundamental: Arquitectura de "Hub & Spoke"
En lugar de un Wizard lineal (`Paso 1 -> Paso 2`), pasaremos a un modelo de **Entidades Independientes** que se relacionan.

*   **Librería de Avatares:** Creas N avatares (ej: "Marca Global", "Nicho Médicos", "Nicho High Ticket").
*   **Librería de Ofertas:** Creas N ofertas, y a cada una le *asignas* un Avatar (o hereda el global).
*   **Edición No-Lineal:** Puedes entrar a editar el precio de una oferta, luego saltar a ajustar el prompt del avatar, sin perder estado.

---

## 2. Refactorización Backend (Modelado de Datos)

Modificaremos `backend/src/services/db/models/business.py` para romper la rigidez actual.

### A. `AvatarDefinition` (Multi-Instancia)
*   **Cambio:** Eliminar `unique=True` en `user_id`.
*   **Nuevos Campos:**
    *   `name` (String): Para identificarlo en el UI (ej: "Avatar General", "Avatar Médicos").
    *   `is_default` (Boolean): Marca el avatar de respaldo (Marca).
    *   `scope` (Enum): `GLOBAL` vs `OFFER_SPECIFIC`.

### B. `Product` (Vinculación Flexible)
*   **Nuevo Campo:** `avatar_id` (ForeignKey a `AvatarDefinition`, Nullable).
*   **Lógica de Resolución:**
    *   Si `product.avatar_id` existe -> Usa ese Avatar.
    *   Si es `NULL` -> Usa el `AvatarDefinition` donde `is_default=True`.

---

## 3. Refactorización Frontend (UX Modular)

Transformaremos `/offer-studio` en un verdadero "Estudio de Gestión".

### A. Nueva Estructura de Navegación
1.  **Dashboard Principal (`/offer-studio`):**
    *   **Tablero de Control:** Muestra tarjetas de Ofertas activas.
    *   **Acceso Rápido:** Botón "Configurar Avatar Global" (Settings de Marca).
    *   **Lista de Recursos:** Acceso directo a la "Biblioteca de Objeciones" y "Assets".

2.  **Vista de Detalle de Oferta (`/offer-studio/offer/[id]`):**
    *   Layout con **Sidebar Lateral de Contexto** (no tabs superiores lineales).
    *   **Secciones:**
        *   `Resumen`: KPIs y Datos duros (Precio, Nombre).
        *   `Avatar & Personalidad`: Selector "Usar Global" vs "Personalizar".
        *   `Matriz de Objeciones`: Editor específico para esta oferta.
        *   `Knowledge Base`: Assets vinculados.

### B. Componente Clave: "Inheritance Selector"
Para resolver tu duda de "uno general y uno por oferta":
*   En la sección de Avatar de la oferta, pondremos un **Switch/Selector**:
    *   Opción A: **"Heredar de Marca"** (Muestra los datos del avatar global en modo lectura).
    *   Opción B: **"Específico para esta Oferta"** (Desbloquea los inputs o permite seleccionar otro avatar de la librería).

---

## 4. Plan de Ejecución (Refactor)

1.  **DB Migration (Backend):**
    *   Alterar tabla `avatar_definitions`: Drop constraint unique, add `name`, `is_default`.
    *   Alterar tabla `products`: Add `avatar_id`.

2.  **Frontend (Offer Studio 2.0):**
    *   Eliminar `OfferWizard` (o refactorizarlo solo para el "Create Flow" inicial).
    *   Crear `OfferDashboard` (Grid de ofertas).
    *   Crear `OfferEditorLayout` (Sidebar navigation).

3.  **Lógica RAG (Ajuste menor):**
    *   El `KnowledgeService` ya soporta `scope`, así que solo debemos asegurar que al buscar contexto, si la oferta usa un avatar específico, busquemos documentos taggeados con ese `avatar_id`.

Esta arquitectura te da la flexibilidad total: cambias el precio hoy, mañana ajustas el avatar del nicho, y pasado mañana subes un nuevo PDF, todo sin flujos forzados.
