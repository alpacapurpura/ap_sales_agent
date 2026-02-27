# Sistema de URLs Públicas Seguras y Página de Reservas

He actualizado el plan para cumplir estrictamente con los nuevos requisitos de seguridad, trazabilidad y generación de URLs únicas para ventas. Implementaremos una arquitectura basada en "Shareable Links" (Enlaces Compartibles) que actúe como capa de seguridad sobre la funcionalidad de reservas.

## 1. Backend: Sistema de "Shareable Links" Seguros

Implementaremos un sistema centralizado para la gestión de URLs públicas.

### Modelo de Datos (`backend/src/services/db/models/link.py`)
Crearemos una nueva tabla `shareable_links` para gestionar el ciclo de vida de los enlaces:
*   `token` (String, Unique, Index): El identificador único (ej. `abc123def456`).
*   `tenant_id`: Para asociar al cliente.
*   `target_type`: Tipo de recurso (ej. `'booking_calendar'`).
*   `params`: JSONB para parámetros codificados y futuros (source, campaign_id).
*   `is_active`: Para revocación inmediata.
*   `expires_at`: Para validez temporal.
*   `visit_count`: Auditoría básica de accesos.

### Servicio de Generación (`LinkService`)
*   **Generación:** Algoritmo que combina UUID parcial + Timestamp para garantizar unicidad y colisiones nulas.
*   **Seguridad:** Validación de integridad y estado activo antes de resolver.

### API Router (`/api/v1/public`)
*   `GET /public/resolve/{token}`: Valida el token, registra la visita (auditoría) y devuelve la configuración del tenant necesaria para el frontend.
*   `POST /public/book/{token}`: Endpoint seguro para realizar la reserva, validando que el token sea válido y corresponda al tenant.

## 2. Frontend: Landing Pública Dinámica

En lugar de exponer el ID del tenant directamente, usaremos una ruta basada en el token seguro.

### Página Pública (`frontend/src/app/visit/[token]/page.tsx`)
*   **Ruta:** `https://midominio.com/visit/{token}`
*   **Lógica:**
    1.  Al cargar, consulta `GET /public/resolve/{token}`.
    2.  Si es válido, renderiza el componente de **Calendario/Reservas**.
    3.  Si es inválido/expirado, muestra página de error 404/410.
*   **SEO:** Implementación de `<meta name="robots" content="noindex" />`.

### Integración en Dashboard (`Connections` Page)
*   Añadiremos una sección en la página de conexiones para:
    1.  Generar una nueva URL única ("Copiar Link de Ventas").
    2.  (Opcional para MVP) Ver/Revocar enlaces activos.

## 3. Testing y Validación
*   **Test de Unicidad:** Script para generar 1000 tokens y verificar colisiones.
*   **Validación de Acceso:** Verificar que un token revocado retorne 403/404.

---
Este enfoque cumple con la "Implementación Inmediata para Ventas" solicitada, proporcionando URLs seguras, auditables y revocables.
