Para mejorar la edición de categorías en el "Inventario de Documentos" y cumplir con el requisito de usar un desplegable con un máximo de 3 selecciones, implementaré los siguientes cambios en `src/admin/app.py`:

### 1. Actualizar `st.column_config.ListColumn` a `SelectboxColumn`
Actualmente, se usa `ListColumn`, que permite texto libre. Lo cambiaré por `st.column_config.SelectboxColumn` (o mantendré `ListColumn` si `SelectboxColumn` no soporta selección múltiple nativa en la versión actual de Streamlit, pero Streamlit soporta `ListColumn` con opciones predefinidas en versiones recientes).
*   **Investigación rápida**: `SelectboxColumn` es para selección única. Para múltiples etiquetas, `ListColumn` es correcto, pero no limita las opciones. Sin embargo, dado que `st.data_editor` es limitado en validaciones complejas en tiempo real, la mejor aproximación es usar `ListColumn` pero validar al guardar.
*   **Corrección de enfoque**: Streamlit `data_editor` no tiene un "MultiselectColumn" nativo que restrinja opciones estrictamente en la UI de la tabla (aún).
*   **Alternativa UI**: La forma más robusta es mantener `ListColumn` (que permite editar como lista) y validar estrictamente en el botón "Guardar Cambios".
*   **Mejora UX**: Si el usuario quiere ver las opciones disponibles, las mostraré en un `st.info` o `st.expander` justo encima de la tabla para que sepa qué escribir (o copiar/pegar), ya que `data_editor` no ofrece un dropdown de autocompletado para listas de strings por defecto.

**Espera**, revisando la documentación más reciente de Streamlit, `SelectboxColumn` es para "Categorical", pero es *single choice*.
Si el usuario quiere *múltiples* categorías (hasta 3), `ListColumn` es la vía, pero la UI de edición es texto libre separado por comas.

**Nueva Estrategia (UX Superior)**:
Dado que editar una lista dentro de una celda es incómodo y propenso a errores, y `data_editor` tiene limitaciones:
1.  Mantendré la columna "Categoría" como **solo lectura** en la tabla principal.
2.  Agregaré una columna `Seleccionar` (checkbox) para elegir **un** documento a editar.
3.  Debajo de la tabla, mostraré un formulario de edición para el documento seleccionado:
    *   `st.multiselect("Editar Categorías", options=VALID_CATEGORIES, default=current_cats, max_selections=3)`
    *   Esto cumple perfectamente con "desplegable", "opciones válidas" y "máximo 3".
4.  Botón "Guardar Cambios" específico para esa selección.

Esta es una solución mucho más limpia y menos propensa a errores que intentar forzar validaciones en una celda de tabla editable.

### Plan Detallado:
1.  Modificar `render_inventory_view`:
    *   Cambiar `st.data_editor` para que la columna "Categoría" sea de lectura.
    *   Agregar columna "Editar" (Checkbox) que funcione como selector único (usando `st.radio` o lógica de checkbox único).
2.  Crear sección "Zona de Edición" debajo de la tabla:
    *   Si hay un documento seleccionado, mostrar `st.multiselect` con `VALID_CATEGORIES`.
    *   Configurar `max_selections=3`.
    *   Botón de guardado que llama a `DocumentService` y `VectorStore`.

Este enfoque es técnicamente superior y ofrece mejor UX.