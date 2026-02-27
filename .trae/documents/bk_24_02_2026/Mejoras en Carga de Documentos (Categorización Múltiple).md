Entendido. Para asegurar que la selección sea clara, añadiré una **Guía Visual de Categorías** directamente en la interfaz.

Dado que el selector múltiple estándar no permite "tooltips" individuales por opción, implementaré la siguiente solución de UX:

### 🚀 Plan Refinado con Guía de Usuario

#### 1. Actualizar `src/admin/app.py`
*   **Selector Inteligente:** Implementaré `st.multiselect` para las categorías.
*   **Componente de Ayuda (Hints):** Agregaré un bloque desplegable **"ℹ️ Guía de Categorías"** justo encima del selector. Al abrirlo, mostrará una tabla clara:
    *   `product`: Promesa, módulos, entregables.
    *   `avatar`: Dolores, deseos, perfil del cliente.
    *   `financial`: Precios, planes de pago, ROI.
    *   `sales_strategy`: Scripts, manejo de objeciones, funnel.
    *   `operations`: Agenda, horarios, logística, facturación.
    *   `legal`: Garantías, reembolsos, contratos.
    *   `brand`: Historia, tono de voz, manifiesto.
*   **Compatibilidad:**
    *   **Qdrant:** Recibe lista `["financial", "operations"]`.
    *   **Postgres:** Recibe string `"financial,operations"`.

De esta forma, tendrás un "chivo expiatorio" (cheat sheet) siempre visible al momento de cargar los documentos para no dudar qué etiqueta usar.