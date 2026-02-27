# Checklist

- [x] Sidebar navigation does NOT show "Conexiones".
- [x] `/settings` page loads without errors.
- [x] Settings sidebar displays "Principal", "Canales de Venta", "Cierre de ventas", and "Desarrolladores" sections.
- [x] Clicking "WhatsApp" tab renders the `WhatsAppView` component.
- [x] Clicking "Perfil" tab renders the `ProfileView` component.
- [x] Clicking "Webhooks" tab renders the `WebhookView` component.
- [x] URL updates correctly when switching tabs (e.g., `/settings?tab=whatsapp`).
- [x] Direct navigation to `/settings?tab=whatsapp` opens the correct tab.
- [x] Google OAuth popup callback logic works (code/error params in URL trigger postMessage).
