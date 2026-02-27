# Implementar Sidepanel de Detalles de WhatsApp

Voy a refactorizar la vista de WhatsApp para mejorar la experiencia de usuario (UX) utilizando un panel lateral (**Sheet**) para mostrar los detalles de la conexión y la opción de desconexión, manteniendo la interfaz limpia y consistente con el resto de la plataforma.

## 1. Frontend: Componente de Detalles (Sidepanel)
Implementaré un `Sheet` de Shadcn UI que se abrirá al hacer clic en "Ver detalles" en la tarjeta de "Modo Sincronizado".

### Estructura del Panel:
*   **Encabezado:** "Estado de Conexión" con indicador visual (punto verde).
*   **Perfil de WhatsApp:**
    *   Foto de perfil (Avatar grande).
    *   Nombre de usuario (PushName).
    *   Número de teléfono (formateado).
*   **Metadatos Técnicos:**
    *   **Estado:** "Sincronizado y escuchando mensajes".
    *   **Proveedor:** "Evolution API (Motor v1.8.2)".
    *   **Instancia:** ID del Tenant.
    *   **Fecha de conexión:** Se mostrará si está disponible (requiere actualización en backend).
*   **Zona de Peligro (Footer):**
    *   Botón "Desconectar Sesión" (Destructive), movido aquí para evitar desconexiones accidentales.

## 2. Backend: Enriquecimiento de Datos
Para que el panel muestre información real (no solo "WhatsApp User"), actualizaré la lógica de `get_whatsapp_status`:

*   **Autoreparación de Metadatos:** Si la conexión está activa (`open`) pero la base de datos no tiene los datos del perfil (nombre, foto), el sistema intentará obtenerlos automáticamente de la instancia y guardarlos.
*   **Persistencia:** Asegurar que el `pushName` y `jid` se guarden en la configuración del Tenant para que estén disponibles siempre.

## Pasos de Implementación
1.  **Backend (`whatsapp.py`):** Mejorar el endpoint `/status` para recuperar y guardar metadatos si faltan.
2.  **Frontend (`whatsapp-view.tsx`):**
    *   Importar componentes `Sheet`.
    *   Crear sub-componente `ConnectionDetailsSheet` para mantener el código limpio.
    *   Actualizar la tarjeta principal para que solo muestre un resumen elegante y el botón de apertura del panel.

Esta solución cumple con el requerimiento de ocultar la opción de desconectar y exponer todos los datos técnicos disponibles.