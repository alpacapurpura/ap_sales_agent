Entendido. Quieres que en la vista de Auditoría, en la sección donde se despliegan los detalles de cada nodo de ejecución (trazas), aparezca una columna lateral (o panel adyacente) que muestre explícitamente **qué datos nuevos del usuario se descubrieron** en ese paso específico.

Esto es muy útil para ver rápidamente *dónde* el agente aprendió que el usuario es "abogado" o que su dolor es "falta de tiempo", sin tener que leer todo el JSON.

### Plan de Implementación

1.  **Modificar `get_state_diff`**:
    *   Actualmente esta función ya detecta cambios en diccionarios anidados.
    *   Me aseguraré de que identifique específicamente cambios en `user_profile` y los devuelva en un formato fácil de renderizar.

2.  **Actualizar `render_audit_view` en `src/admin/app.py`**:
    *   Cambiaré la estructura dentro del bucle de trazas (`for item in timeline`).
    *   Usaré `st.columns([3, 1])` dentro del expander de cada traza:
        *   **Columna Izquierda (3/4)**: Mantendrá la información técnica actual (JSONs, Logs LLM, Diffs generales).
        *   **Columna Derecha (1/4)**: Aquí renderizaré una "Tarjeta de Aprendizaje" (Learning Card) si hubo actualizaciones en el perfil.
            *   Si `user_profile` cambió, mostraré los campos nuevos o modificados con un estilo visual destacado (ej. `st.success` o `st.info`).
            *   Si no hubo aprendizaje sobre el usuario, esta columna quedará vacía o mostrará un indicador sutil.

### Resultado Visual Esperado
Cuando abras el expander de un nodo (ej. `manager`), si el agente extrajo `business_industry: "Marketing"`, verás a la derecha un bloque que dice:
**🧠 Aprendizaje del Usuario**
*   `business_industry`: `Marketing`

Esto cumple exactamente con tu requerimiento de la imagen. Procederé a modificar `src/admin/app.py`.