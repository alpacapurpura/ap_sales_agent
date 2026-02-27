# Plan Final Consolidado: Diccionario de Datos, UX Frontend y Estrategia de Conocimiento

Entendido. Acepto la corrección sobre la arquitectura de conocimiento: existe una distinción clara entre **Conocimiento Global del Tenant** (reutilizable) y **Conocimiento Específico del Producto** (Offer). Aunque la implementación completa de esto es "Fase 2", el plan y la documentación reflejarán esta separación para no generar deuda técnica conceptual.

Este plan generará el documento maestro `docs/architecture/tenant_onboarding_ux_plan.md` con la visión completa.

## 1. Inventario de Campos y Mapeo UX (End-to-End)

El documento clasificará los datos en tres niveles de jerarquía, indicando dónde deben vivir en la UI actual del Admin Panel.

### Nivel 1: Identidad del Tenant (Configuración Global)
*   **Ubicación UI:** Sección "Tenants" > Editar > Pestaña "Identidad".
*   **Campos en `Tenant.config_json`:**
    *   `company_name`: Nombre legal/comercial.
    *   `agent_persona`: Nombre del Bot.
    *   `agent_role`: Rol profesional.
    *   `tone`: Tono de voz.
    *   `sales_protocol`: Estilo de venta (Sandler/Consultivo).

### Nivel 2: Reglas de Negocio (Configuración Operativa)
*   **Ubicación UI:** Sección "Tenants" > Editar > Pestaña "Negocio".
*   **Campos en `Tenant.config_json`:**
    *   `currency`: Moneda predeterminada (PEN/USD).
    *   `authority_figures`: Nombres de expertos (para autoridad).
    *   `payment_link_template`: (Opcional) Template base para links.

### Nivel 3: Base de Conocimiento (Knowledge Hub)
*   **Ubicación UI:** Sección "Conocimiento".
*   **Estrategia de Separación (Scope):**
    *   **Global (Tenant Scope):** Documentos "Brand Voice", "Filosofía", "Casos de Éxito Generales". Se suben en la vista principal de Conocimiento asociándolos al Tenant.
    *   **Offer Specific (Product Scope - Fase 2):** Documentos "Precios", "Temario", "Fechas". En el futuro, estos se subirán *dentro* de la ficha de edición de un Producto específico.
    *   **UX Actual:** Mantener el uploader en "Conocimiento" pero añadir un selector claro: *"¿Es conocimiento Global o de un Producto?"* (Preparado para Fase 2).

## 2. Documentación Entregable
El documento Markdown incluirá:
1.  **Tabla Maestra de Campos:** Clave DB, Tipo de Dato, Obligatoriedad, Default, Descripción UX.
2.  **Mapa de Calor UX:** Dónde ubicar cada campo en la estructura actual de `app.py` para que sea intuitivo ("Orgánico").
3.  **Nota de Arquitectura:** Explicación explícita de la separación `GLOBAL` vs `OFFER` en Qdrant y cómo el Frontend debe manejarlo (selector de Scope).

## 3. Ejecución
Generaré el archivo `docs/architecture/tenant_onboarding_ux_plan.md` siguiendo estrictamente estas directrices.

¿Procedo?