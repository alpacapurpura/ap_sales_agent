Entendido. Quieres restaurar la visibilidad de los prompts renderizados en la auditoría y limpiar la visualización de la línea de tiempo para que sea una herramienta de depuración verdaderamente útil, inspirada en las mejores prácticas (como Flowise).

### Problemas Detectados
1.  **Prompts Ocultos**: Al intentar mejorar el diseño, la sección de `LLM Logs` donde se mostraban los prompts renderizados quedó anidada o condicionada de tal forma que ya no es fácilmente visible o accesible.
2.  **Ruido en la Línea de Tiempo**: Mencionas que "se repite a cada rato la actualización de estados". Esto suele pasar cuando el `get_state_diff` es demasiado sensible o cuando los nodos re-emiten el mismo estado sin cambios reales, llenando la auditoría de "ruido" visual.
3.  **Reseteo de Valores**: "Se le da un valor y vuelve a setearse a none". Esto indica que el `get_state_diff` podría estar comparando mal o mostrando actualizaciones nulas innecesarias.

### Plan de Solución

#### 1. Restaurar y Mejorar Logs de LLM (Prompts)
-   Voy a mover la sección de `LLM Logs` fuera de condicionales complejos y asegurarme de que siempre se muestre si existen logs.
-   Usaré un componente visual claro (ej. `st.info` o un expander dedicado con un icono llamativo 🤖) para que el Prompt y la Respuesta del modelo sean protagonistas.

#### 2. Limpieza de "Ruido" en el Diff de Estado
-   Modificaré `get_state_diff` para ser más inteligente:
    -   Ignorar cambios de `None` a `None`.
    -   Ignorar claves internas irrelevantes si no aportan valor al debug.
-   En la visualización, filtraré los cambios que son solo "ruido" (ej. re-escritura del mismo valor).

#### 3. Estructura "Flowise-style"
-   Rediseñaré el bloque de cada nodo en la línea de tiempo para que se vea como una "tarjeta" de paso:
    -   **Cabecera**: Nombre del Nodo + Tiempo + Icono de Estado.
    -   **Cuerpo Principal**:
        -   **Input**: Resumen de entrada (si aplica).
        -   **Proceso**: Aquí irán los Prompts renderizados (Lo que "pensó" o se le pidió al LLM).
        -   **Output**: La respuesta generada o el cambio de estado.
    -   **Lateral (Derecha)**: Mantendré la columna de "Aprendizaje del Usuario" que acabamos de hacer, ya que es útil, pero asegurando que no se solape con los prompts.

### Ejecución
Modificaré `src/admin/app.py` para reestructurar la función `render_audit_view` y `get_state_diff`.