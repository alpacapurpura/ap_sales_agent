# Guía de Interpretación: EventDetails para Agentes IA

Este documento define la lógica de negocio y comportamiento esperado del Agente IA al interactuar con ofertas del tipo `EventDetails` (Webinars, Retiros, Masterminds).

## Concepto
`EventDetails` modela **Experiencias en Tiempo y Espacio**.
*   **Filosofía**: "Momento Único + Ubicación Específica".
*   **Complejidad Logística**: Alta (Viajes, Hoteles, Zonas Horarias).
*   **Rol del Agente**: "Host Virtual" o "Concierge de Viajes".

---

## 1. Interpretación de Coordenadas (Tiempo y Espacio)

### A. Gestión Temporal (Timezone)
El Agente SIEMPRE debe considerar la zona horaria del usuario vs la del evento.
*   **Dato**: `timezone` (ej. 'America/Mexico_City').
*   **Acción IA**: Al confirmar, convertir la hora al local del usuario si es posible, o ser explícito: *"Te esperamos a las 10:00 AM hora Ciudad de México"*.

### B. Motor de Ubicación (Location Engine)

#### Escenario 1: El Webinar (Virtual)
*   **Datos**: `location_type=VIRTUAL`, `virtual_meeting_url=Zoom`, `is_recorded=True`.
*   **Rol IA**: Host Técnico.
*   **Lógica**:
    1.  **Entrega**: Enviar link de Zoom inmediatamente.
    2.  **Manejo de Objeción "No puedo ir"**: "No te preocupes, como dice la oferta, *sí* quedará grabado y te enviaré el replay."

#### Escenario 2: El Taller Local (Físico)
*   **Datos**: `location_type=IN_PERSON`, `venue_name=Hotel Hilton`, `map_link=...`.
*   **Rol IA**: Anfitrión Local.
*   **Lógica**:
    1.  **Logística**: Enviar mapa y dirección exacta.
    2.  **Recordatorio**: "El registro abre 30 minutos antes en el lobby del [venue_name]."

#### Escenario 3: El Retiro de Lujo (Retiro en Destino)
*   **Datos**: `location_type=RETREAT`, `accommodation=LUXURY_SUITE`, `airport=CUN`.
*   **Rol IA**: Concierge de Viajes.
*   **Lógica Compleja**:
    1.  **Venta**: "Tu ticket incluye [accommodation_type], así que no te preocupes por el hotel."
    2.  **Logística de Vuelo**: "El aeropuerto más cercano es [recommended_airport_code]. ¿Necesitas ayuda coordinando tu llegada?"
    3.  **Traslado**: Si `is_transfer_included=True`: "Nuestro chofer te esperará en la terminal."

---

## 2. Experiencia del Participante

Usa los detalles finos para cerrar la venta emocional.

*   **`agenda_highlights`**: No vendas "3 días de conferencias". Vende "Cena de Blanco en la playa" y "Yoga al amanecer".
*   **`dress_code`**: Ayuda a visualizar la experiencia. "Prepara tu mejor outfit [dress_code]."

---

## 3. Validaciones de Negocio (Guardrails)

La IA rechazará configuraciones incoherentes para proteger la operación:

*   ❌ **Evento Físico sin Lugar**: No se puede vender un evento presencial sin decir DÓNDE es (`venue_name`).
*   ❌ **Evento Virtual con Dirección Física**: Confunde al usuario.
*   ❌ **Fechas Imposibles**: El evento no puede terminar antes de empezar.

---

## Resumen de Reglas de Oro

1.  **Virtual = Link de Zoom**.
2.  **Físico = Mapa y Lugar**.
3.  **Retiro = Resolver dudas de Hotel y Vuelos**.
4.  **Siempre aclarar la Zona Horaria**.
