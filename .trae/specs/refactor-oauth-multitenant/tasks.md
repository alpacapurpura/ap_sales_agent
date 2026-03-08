# Tasks

- [ ] Task 1: Refactor Google Analytics (Backend + Frontend)
  - [ ] SubTask 1.1: **Backend**: Implementar `PUT /config` en `api/google_analytics.py` y actualizar Adapter para usar credenciales dinámicas.
  - [ ] SubTask 1.2: **Frontend**: Modificar `google-analytics-view.tsx` para agregar formulario de Client ID/Secret y lógica de estados (Configurado vs No Configurado).

- [ ] Task 2: Refactor Meta Business Suite (Backend + Frontend)
  - [ ] SubTask 2.1: **Backend**: Implementar `PUT /config` en `api/meta.py` y actualizar Adapter.
  - [ ] SubTask 2.2: **Frontend**: Modificar `meta-view.tsx` para agregar formulario de App ID/Secret.

- [ ] Task 3: Refactor YouTube (Backend + Frontend)
  - [ ] SubTask 3.1: **Backend**: Implementar `PUT /config` en `api/youtube.py` y actualizar Adapter.
  - [ ] SubTask 3.2: **Frontend**: Modificar `youtube-view.tsx` para agregar formulario de Client ID/Secret.

- [ ] Task 4: Verification
  - [ ] SubTask 4.1: Verificar que Shopify, MailerLite y ManyChat siguen funcionando correctamente (Regression Test).
  - [ ] SubTask 4.2: Verificar flujo completo de OAuth con credenciales propias.

# Task Dependencies
- Backend debe actualizarse antes que Frontend para cada tarea.
