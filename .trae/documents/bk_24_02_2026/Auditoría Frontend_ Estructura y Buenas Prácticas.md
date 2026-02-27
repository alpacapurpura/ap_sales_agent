# Plan de Refactorización y Estandarización Frontend

Basado en la auditoría realizada y tu solicitud, procederemos a limpiar la deuda técnica detectada y actualizar las reglas del proyecto para evitar que esto vuelva a ocurrir.

## 1. Actualización de Reglas (`.trae/rules/front-structure.md`)
Actualizaremos la documentación viva del proyecto para reflejar los estándares de calidad exigidos.
*   **Centralización de Tipos:** Definir explícitamente que los tipos de dominio deben vivir en `src/lib/api` o `src/types`, prohibiendo re-declaraciones en componentes.
*   **Manejo de Mocks:** Establecer `src/lib/mocks` como el lugar para datos de prueba.
*   **Server vs Client:** Reforzar el patrón "Server Page -> Client Component".

## 2. Refactorización de Código (Limpieza)
Aplicaremos los cambios para eliminar la redundancia detectada:

*   **Paso 1: Unificar Interfaces en `src/lib/api/offer.ts`**
    *   Asegurar que `Objection`, `MarketingAsset` y `AvatarDefinition` estén completas y exportadas correctamente.
*   **Paso 2: Limpiar Componentes (`offer-studio`)**
    *   Modificar `objection-editor.tsx`: Eliminar interface local e importar desde `lib/api`.
    *   Modificar `asset-uploader.tsx`: Eliminar interface local e importar desde `lib/api`.
    *   Modificar `inheritance-selector.tsx` y otros componentes si aplica.
*   **Paso 3: Extracción de Mocks (Opcional pero recomendado)**
    *   Si el código lo permite fácilmente, moveremos los datos hardcoded a un archivo centralizado, aunque la prioridad es la limpieza de Tipos.

## 3. Verificación
*   Confirmar que el build (`npm run build` o inspección estática) no falla por problemas de tipos.
*   Verificar que la aplicación sigue funcionando idénticamente (refactor seguro).

---
**Procederé inmediatamente con la actualización de las reglas y la limpieza de tipos.**
