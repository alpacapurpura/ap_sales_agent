# Unificación de Leads e Identidades para Marketing 360

## Conceptual Model: ¿Por qué 3 Tablas?

Para cumplir con tu visión de "aprender del cliente en cada conversación" y "no duplicar información", separamos **Quién es** (Cliente), **Cómo lo contactamos** (Identidad) y **Qué le estamos vendiendo** (Lead).

### 1. CustomerProfile (La Persona)
*   **Qué es**: El registro único de "Juan Pérez".
*   **Rol**: Almacena la "Verdad Central". Datos que no cambian con cada venta: Nombre, Gustos, Preferencias, LTV (Valor de Vida), Nivel de Fidelidad.
*   **Por qué separado**: Si Juan compra hoy y vuelve en 6 meses, no queremos "re-aprender" quién es. El agente consultará esta tabla para decir: *"Hola Juan, ¿qué tal te fue con el producto X que compraste en enero?"*.

### 2. CustomerIdentity (Las Llaves de Acceso)
*   **Qué es**: Los identificadores de Juan en el mundo digital (WhatsApp +52..., Email juan@gmail.com, TelegramID 12345).
*   **Rol**: Permite la **Omnicanalidad**.
*   **Por qué separado**:
    *   Si Juan pierde su celular y cambia de número, solo actualizamos su Identidad. Su historial (Perfil y Ventas) se mantiene intacto.
    *   Si Juan nos escribe por Telegram por primera vez, el sistema busca en `Identities`. Si no lo encuentra, podemos preguntarle su correo. Si el correo coincide con una identidad existente, **¡Boom! Fusionamos el perfil**.

### 3. Lead (La Oportunidad de Venta)
*   **Qué es**: Una "Ficha de Trámite" o "Ticket" para una venta específica.
*   **Rol**: Gestiona el **Ciclo de Venta Actual**. Tiene un estado (MQL, SQL, Cerrado), un Score de interés y un resumen de *esta* conversación.
*   **Por qué separado**:
    *   Juan puede comprarte un curso hoy (Lead #1 - Cerrado Ganado).
    *   Y preguntar por una consultoría mañana (Lead #2 - En Progreso).
    *   Si mezcláramos todo, al abrir la segunda venta sobrescribiríamos la información de la primera.

---

## Why (Problema Actual)
Actualmente, el sistema trata cada interacción como un `Lead` aislado que contiene su propia identidad (ID de WhatsApp). Esto causa:
1.  **Amnesia del Agente**: Si Juan escribe por otro canal, el agente no sabe quién es.
2.  **Duplicidad**: Al importar bases de datos (ManyChat), se crean "nuevas personas" en lugar de actualizar a las existentes.
3.  **Métricas Rotas**: No puedes calcular el LTV (Valor de Vida) porque las ventas están dispersas en múltiples "Leads" que el sistema no sabe que son la misma persona.

## What Changes

### Base de Datos (PostgreSQL)
-   **Modificar `customer_identities`**: Ampliar `IdentityType` para soportar `whatsapp`, `telegram`, `instagram`, `tiktok`.
-   **Migración de Datos**: Mover los IDs sociales (`telegram_id`, `whatsapp_id`, etc.) de la tabla `leads` a filas en `customer_identities`.
-   **Limpieza de `leads`**: El `Lead` ya no guardará `whatsapp_id`. Solo guardará `customer_id`.

### Backend Logic (Flujo de Reconocimiento)
1.  **Entra Mensaje (Webhook)**: El sistema recibe un mensaje de `+555...` (WhatsApp).
2.  **Búsqueda de Identidad**: ¿Existe `+555...` en `CustomerIdentity`?
    *   **SÍ**: Recuperamos al `CustomerProfile` asociado (Juan).
    *   **NO**: Creamos un `CustomerProfile` temporal y su `Identity`.
3.  **Gestión de Lead**:
    *   Buscamos: ¿Tiene Juan un `Lead` abierto (En proceso)?
    *   **SÍ**: Continuamos esa conversación.
    *   **NO**: Creamos un nuevo `Lead` para esta nueva intención de compra.

## Impact
-   **Affected Specs**: `onboarding`, `sales`, `marketing`.
-   **Affected Code**:
    -   `src/modules/communication/application/orchestrators/chat.py` (Lógica de entrada).
    -   `src/modules/sales/infrastructure/models/lead_model.py` (Schema).
    -   `src/modules/marketing/infrastructure/models/customer.py` (Schema).

## ADDED Requirements

### Requirement: Resolución de Identidad Unificada
El sistema DEBE identificar a un usuario independientemente del canal de entrada.

### Requirement: Dashboard de Marketing (Backend Support)
El sistema DEBE proveer endpoints para consultar las métricas de los 7 nodos del Sankey (Adquisición -> Evangelización).

### Requirement: Documentación de Arquitectura IA
El sistema DEBE incluir un documento técnico (`ARCHITECTURE_IA.md`) que explique la relación entre Customer, Identity y Lead para facilitar el entrenamiento y contexto de futuros agentes de desarrollo.

## MODIFIED Requirements
### Requirement: Creación de Lead
**Antes**: Se creaba un Lead con `whatsapp_id`.
**Ahora**: Se crea (o recupera) un `Customer` con `Identity(whatsapp)`. Luego se crea un `Lead` vinculado a ese `Customer`.

## REMOVED Requirements
### Requirement: Identificadores en Tabla Leads
**Reason**: Normalización. Los identificadores pertenecen a la Identidad del Cliente.
**Migration**: Script de Alembic moverá los datos existentes.
