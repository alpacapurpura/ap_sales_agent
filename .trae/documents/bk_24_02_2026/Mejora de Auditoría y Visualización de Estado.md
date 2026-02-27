Voy a mejorar la sección "Auditoría de Conversaciones" en `src/admin/app.py` integrando la visualización de cambios sin perder el acceso a los datos crudos.

### 1. Visualización de Cambios en AgentState
Implementaré una vista híbrida para cada traza de ejecución:

- **Resumen de Cambios (Diff)**: Al abrir el expander de una traza, verás primero un resumen visual de lo que cambió:
    - Transiciones de Estado (`S1 -> S2`).
    - Nuevos datos capturados en el perfil.
    - Decisiones de ruteo (`router_outcome`).
- **Inspector JSON Completo**: Mantendré la visualización de los JSONs de entrada y salida (como solicitaste) para que puedas ver la totalidad de la información viajando. Los organizaré en pestañas o columnas debajo del resumen para facilitar la lectura.

### 2. Panel de Datos Persistentes del Usuario
Agregaré un panel superior fijo en la vista de auditoría con los datos "vivos" de la base de datos:

- **Tarjeta de Usuario**: Datos de contacto e identificadores.
- **Perfil Psigráfico (Profile Data)**: Visualización estructurada (JSON o Tabla) de `User.profile_data` para ver la "foto final" del usuario.
- **Estado del Funnel**: Etapa y Score actual.

### 3. Implementación Técnica
Modificaré `src/admin/app.py`:
1.  **Función `render_state_diff(input, output)`**: Calculará y mostrará las diferencias clave.
2.  **Actualizar `render_audit_view`**:
    - Insertar el panel de usuario al principio.
    - En cada item del timeline (Traza), mostrar: `Diff` -> `JSONs (Input/Output)` -> `LLM Logs`.

Esto te dará lo mejor de ambos mundos: comprensión rápida de la lógica y profundidad técnica para debugging.