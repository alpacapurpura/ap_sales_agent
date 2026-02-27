Refactorización de la sección "Sobre la Marca" para dividir la gestión de Autoridad en dos pestañas independientes bajo un nuevo grupo.

## Pasos de Implementación

1.  **Crear Componente `KeyFiguresForm`**
    *   Ubicación: `frontend/src/components/brand/key-figures-form.tsx`
    *   Contenido: Extraer la lógica de "Lista de Personas Clave" (estado `team`, modales de edición, renderizado de tarjetas) desde `AuthoritySquadForm`.
    *   Props: `initialData`, `onSave`, `isSaving`.

2.  **Crear Componente `AuthorityVaultForm`**
    *   Ubicación: `frontend/src/components/brand/authority-vault-form.tsx`
    *   Contenido: Extraer la lógica de "Lista de Respaldo Institucional" (estado `vault`, modales de edición, renderizado de tarjetas) desde `AuthoritySquadForm`.
    *   Props: `initialData`, `onSave`, `isSaving`.

3.  **Actualizar `BrandSettingsPage`**
    *   Ubicación: `frontend/src/app/(dashboard)/brand-settings/page.tsx`
    *   Acción:
        *   Implementar nuevos handlers `handleSaveTeam` y `handleSaveVault` que actualicen partes específicas de la configuración global.
        *   Modificar la barra lateral de pestañas (`TabsList`):
            *   Añadir nuevo encabezado de grupo **"Autoridad"**.
            *   Añadir pestañas **"Key Figures"** y **"Respaldo Institucional"**.
            *   Eliminar la pestaña antigua "Autoridad y Equipo".
        *   Integrar los nuevos componentes en `TabsContent`.

4.  **Limpieza de Código**
    *   Eliminar el archivo obsoleto `frontend/src/components/brand/authority-squad-form.tsx`.
    *   Verificar que no queden importaciones rotas.

## Resultado Esperado
Una estructura de navegación más granular en "Sobre la Marca", con un nuevo grupo "Autoridad" que contiene pestañas dedicadas para el Equipo y el Respaldo Institucional, mejorando la organización y la experiencia de usuario.