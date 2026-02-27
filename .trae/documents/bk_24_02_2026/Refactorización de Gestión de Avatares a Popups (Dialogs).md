Voy a transformar la experiencia de creación y edición de Avatares para que funcione mediante ventanas emergentes (Popups) dentro de la misma página, manteniendo el contexto del usuario y replicando el estilo visual del módulo "Agregar Persona".

### Pasos de Implementación:

1.  **Adaptar el Formulario de Avatar (`AvatarForm`)**:
    *   Modificaré `frontend/src/components/avatars/avatar-form.tsx` para aceptar una nueva propiedad `embedded` (incrustado).
    *   Cuando `embedded={true}`, el formulario se renderizará sin el marco de tarjeta (`Card`) ni el título interno, permitiendo que se integre limpiamente dentro del Popup (Dialog), igual que en "Agregar Persona".

2.  **Integrar el Popup en el Gestor (`AvatarManager`)**:
    *   Modificaré `frontend/src/components/brand/avatar-manager.tsx`.
    *   Añadiré los componentes de `Dialog` (Popup) de Shadcn UI.
    *   Implementaré el estado local para controlar la apertura del popup y el avatar seleccionado (`editingAvatar`).
    *   Configuraré las mutaciones de API (`createMutation` y `updateMutation`) directamente en este componente, ya que ahora la lógica de guardado ocurrirá aquí y no en una página separada.

3.  **Actualizar la Interacción**:
    *   El botón **"Nuevo Avatar"** abrirá el popup con el formulario vacío.
    *   El botón **"Editar"** (lápiz) abrirá el mismo popup precargado con los datos del avatar.
    *   Se eliminarán las redirecciones a `/avatars/new` y `/avatars/[id]`.

### Resultado Esperado:
El usuario podrá crear y editar avatares sin salir de la pestaña "Avatares" en la configuración de marca, con una interfaz visualmente consistente con el resto del panel.