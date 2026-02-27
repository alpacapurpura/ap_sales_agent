# Communication Module Refactoring Spec

## Why
El módulo Communication maneja la interacción con canales externos (Telegram, WhatsApp, etc.) y citas. Actualmente, los modelos de dominio están mezclados con los de infraestructura. `ChannelConnection` tiene lógica de `Base` (SQLAlchemy) en `domain/channel_connection.py`. Se requiere desacoplar el dominio de la persistencia y estandarizar los Enums.

## What Changes
-   **Domain**:
    -   `Message`: Entidad pura (Pydantic).
    -   `ChannelConnection`: Entidad pura.
    -   `Appointment`: Entidad pura.
    -   `Enums`: `ChannelType`, `MessageSender`, `AppointmentStatus`.
-   **Infrastructure**:
    -   `MessageModel`, `ChannelConnectionModel`, `AppointmentModel` (SQLAlchemy) en `infrastructure/models/`.
    -   `MessageRepository`, `ChannelRepository`, `AppointmentRepository`.
-   **Application**:
    -   `MessageService`: Gestión de mensajes (guardar, recuperar historial).
    -   `ChannelService`: Gestión de conexiones.
-   **API**:
    -   `webhooks_cdp.py`: Actualizar para usar servicios.

## Impact
-   **Affected Code**: `src/modules/communication/*`.
-   **Breaking Changes**: Rutas de importación.

## ADDED Requirements

### Requirement: Communication Domain
-   `Message`: ID, Content, Sender, Channel, Metadata.
-   `ChannelConnection`: Credentials (JSON), Config (JSON).

### Requirement: Communication Infrastructure
-   Modelos SQLAlchemy heredando de `Base`.
-   Repositorios manejan JSONB.

### Requirement: Communication Application
-   `MessageService.save_message(content, sender, lead_id) -> Message`
-   `MessageService.get_history(lead_id) -> List[Message]`
