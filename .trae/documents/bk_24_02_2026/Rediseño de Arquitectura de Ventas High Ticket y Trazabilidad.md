# Plan de Rediseño: Arquitectura de Ventas High Ticket

## 1. Actualización de Modelos de Datos (src/services/models.py)
Reconstruiremos el esquema para soportar trazabilidad profunda.

### Tabla `Product` (Mejorada)
- Agregar campo `tier`: `Enum("lead_magnet", "tripwire", "high_ticket")`.
- **Acción:** Definir explícitamente:
    1. "Programa de propósito a progreso" -> `tier: high_ticket`.
    2. "Webinar para mujeres que quieren emprender" -> `tier: lead_magnet`.

### Nueva Tabla `OfferLog`
Para cumplir con "Tabla de ofrecimientos con relación cliente-producto-fecha".
- `id`: UUID
- `user_id`: FK User
- `product_id`: FK Product
- `offered_at`: DateTime
- `pitch_type`: String (ej. "soft_pitch", "hard_close")
- `response`: String (pending, accepted, rejected)

### Tabla `Message` (Enriquecida)
Para "Conversación guardada junto al thought, intención y agent state".
- Agregar `metadata_log`: JSONB.
- Estructura: `{ "thought": "...", "intent": "...", "current_state": "S3_Gap" }`.

## 2. Lógica de Negocio y Repositorio (src/services/repository.py)
- **Nuevo Método `get_next_best_offer(user_id)`**:
    - Verifica si el usuario ya consumió el Lead Magnet.
    - Si NO -> Retorna Producto Webinar.
    - Si SI -> Retorna Producto High Ticket.
- **Mejora en `log_message`**: Soportar la inyección del JSON de pensamiento.
- **Nuevo Método `log_offer`**: Para registrar en `OfferLog`.

## 3. Inicialización de Datos (src/services/database.py)
- **Reset Completo:** Eliminar datos antiguos.
- **Semilla (Seed):** Insertar los dos productos exactos solicitados con fechas de lanzamiento simuladas para pruebas.

## 4. Endpoints y Agente
- El agente (`nodes.py`) usará `metadata_log` al guardar su respuesta, permitiendo auditar por qué ofreció X producto.

Este diseño garantiza que sepas exactamente **qué se ofreció, cuándo y por qué**.
