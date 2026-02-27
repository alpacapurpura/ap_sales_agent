# Refactorización del Modelo User para Eficiencia

Dado que no tenemos datos que perder, procederemos a limpiar el modelo `User` para alinearlo con el nuevo esquema `UserProfile`.

## 1. Cambios en Base de Datos (`src/services/models.py`)

*   **Eliminar** columna `demographics` (redundante).
*   **Renombrar** columna `psychographics` a `profile_data`.
    *   *Razón*: `psychographics` es un nombre limitante. `profile_data` representará fielmente el contenedor del esquema `UserProfile` (que ahora incluye demografía, psicografía y estado de negocio).
    *   Tipo: `JSONB`. Default: `{}`.

## 2. Actualización de Código (Refactor)

Actualizaré las referencias en el código para usar el nuevo nombre `profile_data`.

### A. `src/services/repository.py`
*   Método `clear_user_conversation`: Limpiar `user.profile_data`.
*   Método `update_user_profile`: Actualizar `user.profile_data` en lugar de `psychographics`.

### B. `src/api/routes.py`
*   Inyección de Estado Inicial: Leer de `user.profile_data` al construir el `AgentState`.

## 3. Verificación
Crearé un script temporal para verificar que el modelo `User` se instancia correctamente y que el campo `profile_data` acepta el diccionario del esquema `UserProfile`.
