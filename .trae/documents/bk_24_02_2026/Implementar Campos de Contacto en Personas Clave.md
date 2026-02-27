# Implementar Nuevos Campos en "Key Figures" (Personas Clave)

Este plan detalla los pasos para agregar los campos de redes sociales y contacto solicitados a la entidad "Key Figure" tanto en el backend como en el frontend.

## Backend: Actualización del Esquema
### `backend/src/core/domain/brand_schema.py`
1.  **Modificar la clase `KeyFigure`**:
    *   Agregar los siguientes campos opcionales con validación de tipo:
        *   `personal_website`: `HttpUrl` (o `str` con validación de URL)
        *   `personal_linkedin`: `HttpUrl`
        *   `personal_instagram`: `HttpUrl`
        *   `personal_tiktok`: `HttpUrl`
        *   `personal_facebook`: `HttpUrl`
        *   `work_whatsapp`: `str` (Campo de texto libre, no URL)

## Frontend: Interfaz y Componentes
### `frontend/src/lib/api/brand.ts`
1.  **Actualizar la interfaz `KeyFigure`**:
    *   Sincronizar la definición de TypeScript con los nuevos campos del backend para asegurar el tipado estricto.

### `frontend/src/components/brand/authority-squad-form.tsx`
1.  **Actualizar Estado Inicial (`openTeamModal`)**:
    *   Inicializar los nuevos campos como cadenas vacías (`""`) al crear una nueva persona.
2.  **Modificar el Modal de Edición ("Team Modal")**:
    *   Agregar una nueva sección visual (ej: "Redes y Contacto") dentro del formulario.
    *   Implementar `Input` fields para cada nuevo dato:
        *   Website, LinkedIn, Instagram, TikTok, Facebook (con validación visual o placeholder de URL).
        *   WhatsApp Trabajo.

## Verificación
1.  **Backend**: Ejecutar `ruff` para validar la sintaxis.
2.  **Frontend**:
    *   Iniciar el servidor de desarrollo.
    *   Navegar a "Sobre la Marca" -> "Autoridad y Equipo".
    *   Intentar crear una nueva persona con todos los campos.
    *   Guardar y recargar para asegurar la persistencia.
