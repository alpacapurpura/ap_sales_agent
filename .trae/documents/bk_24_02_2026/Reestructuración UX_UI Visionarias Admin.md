# Propuesta de Reestructuración UX/UI para Visionarias Admin

Actualmente, la aplicación usa pestañas (`Tabs`) que ocultan la funcionalidad y una barra lateral infrautilizada. Mi propuesta se basa en patrones de diseño de paneles de administración modernos (como los de SaaS tipo HubSpot o plataformas de datos), moviendo la navegación principal a la barra lateral para un acceso rápido y claro.

## 1. Nueva Arquitectura de Navegación (Sidebar)

La barra lateral izquierda (`st.sidebar`) será el **menú principal de navegación**, reemplazando las pestañas superiores. Esto libera espacio vertical y hace que las secciones sean "descubribles".

### Estructura del Menú (Sidebar)

1. **Dashboard** (Inicio)

   * Métricas rápidas (Vectores totales, Documentos indexados, Estado de Qdrant).

   * Accesos directos.
2. **Base de Conocimiento** (Agrupador)

   * 📤 **Cargar Documentos**: Subida, etiquetado y chunking.

   * 📂 **Inventario**: Tabla de gestión, eliminación y estado.

   * 🔍 **Probador RAG**: Buscador de prueba aislado (para validar qué responde el cerebro).
3. **Observabilidad** (Agrupador)

   * 🕵️ **Auditoría de Conversaciones**: El inspector de trazas y chats de usuarios.

   * 📊 **Logs del Sistema**: (Futuro) Logs técnicos.
4. **Configuración** (Abajo del todo)

   * ⚙️ **Ajustes**: Reiniciar base de datos (acción peligrosa), configuración de prompts.

## 2. Mejoras de UX por Sección

### A. Carga de Documentos (Prioridad: Claridad)

* **Problema actual**: Mucho texto y opciones mezcladas.

* **Solución**:

  * Usar `st.expander` para las configuraciones avanzadas (Chunking, Contexto IA) que por defecto estén cerradas.

  * La guía de categorías debe ser un `st.info` o un tooltip `help=` en el selector, no una tabla gigante que ocupa espacio siempre.

### B. Auditoría (Prioridad: Análisis)

* **Problema actual**: Lista plana de usuarios.

* **Solución**:

  * Mantener el selector de usuarios pero agregar filtros rápidos (ej. "Última hora", "Con errores").

  * La línea de tiempo es buena, pero los JSONs crudos (`st.json`) asustan. Usar `st.dataframe` o componentes visuales para mostrar inputs/outputs clave.

## 3. Plan de Refactorización Técnica

1. **Navegación con** **`streamlit-option-menu`** **(Opcional) o** **`st.radio`** **estilizado**: Para manejar el cambio de "páginas" sin recargar todo el script, usaremos una estructura de control de flujo basada en la selección del sidebar.
2. **Modularización**: Mover cada "Página" a una función separada (`render_upload_view()`, `render_audit_view()`, etc.) para limpiar el `app.py` principal.

## Ejemplo Visual de la Propuesta

```text
[SIDEBAR]
----------------
VISIONARIAS BRAIN
----------------
🏠 Dashboard
----------------
KNOWLEDGE BASE
📤 Cargar Docs
📂 Inventario
🔍 Probador RAG
----------------
OBSERVABILITY
🕵️ Auditoría
----------------
⚙️ Configuración
```

