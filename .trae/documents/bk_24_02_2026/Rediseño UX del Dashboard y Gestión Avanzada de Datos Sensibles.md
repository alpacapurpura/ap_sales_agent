# Rediseño UX/UI del Dashboard: Módulo de Conocimiento y Datos Sensibles

He diseñado una reestructuración completa del dashboard, inspirada en la experiencia de usuario (UX) de plataformas modernas como Hostinger y Cloudflare (versión 2026), priorizando la claridad, la jerarquía visual y la facilidad de uso.

## 🎨 Principios de Diseño UX Aplicados
1.  **Navegación Jerárquica:** Agruparemos las funciones dispersas bajo una nueva categoría "Conocimiento (Knowledge Base)", reduciendo el ruido visual en la barra lateral.
2.  **Contexto Guiado (Hints):** Cada campo de entrada tendrá explicaciones claras y ejemplos visuales, reduciendo la carga cognitiva del usuario.
3.  **Segregación de Ámbitos:** Separación clara entre datos de **Marca** (Globales) y **Producto** (Específicos), como solicitaste.

## 🛠️ Plan Técnico

### 1. Actualización del Modelo de Datos (`SensitiveData`)
Para soportar la distinción entre Marca y Producto, necesito enriquecer el modelo en `src/services/db/models/business.py`.
*   **Nuevo campo `scope`:** Enum (`BRAND`, `PRODUCT`).
*   **Nuevo campo `product_id`:** ForeignKey opcional (solo si `scope=PRODUCT`).

### 2. Reingeniería del Frontend (`src/admin/app.py`)

#### A. Nueva Estructura de Navegación (Sidebar)
Reemplazaré la lista plana actual por una estructura agrupada:
*   🏠 **Dashboard**
*   🧠 **Cerebro & Agente** (Auditoría, Prompts, Configuración)
*   📚 **Conocimiento** (Nueva "Super-Sección")

#### B. La Nueva Vista "Conocimiento"
Esta vista será un "Hub" con pestañas internas (Tabs) para una navegación fluida sin recargar la página:

1.  **Tab 1: Biblioteca de Documentos**
    *   Fusión de "Cargar", "Masiva" e "Inventario" en una sola experiencia cohesiva.

2.  **Tab 2: Datos Sensibles (Safety Layer)** 🛡️ *Foco Principal*
    *   **Selector de Ámbito:** Un "Toggle" grande o Tabs secundarias: `🏢 Nivel Marca` vs `🚀 Nivel Producto`.
    *   **Formulario Inteligente:**
        *   Si es `Nivel Producto`, aparece un dropdown para seleccionar el producto activo.
        *   **Categorías Claras:** "Dinero/Precios", "Fechas/Tiempos", "Secretos Comerciales".
        *   **Ayudas Visuales:** "Hints" explicativos (ej: "Usa esto para ocultar márgenes de ganancia").
    *   **Tabla de Reglas:** Visualización limpia con filtros por ámbito.

3.  **Tab 3: Reglas de Negocio** (Placeholder)
    *   Estado "Próximamente".

4.  **Tab 4: Identidad de Marca** (Placeholder)
    *   Estado "Próximamente".

### 3. Implementación
1.  Modificar `src/services/db/models/business.py` (Schema update).
2.  Refactorizar masivamente `src/admin/app.py` para implementar la nueva lógica de navegación y las vistas detalladas.

Este enfoque no solo cumple con tus requisitos funcionales, sino que eleva la calidad del producto a un estándar SaaS profesional.
