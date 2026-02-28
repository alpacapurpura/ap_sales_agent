"""
Módulo de Comunicación y Canales Externos.

Responsabilidad:
    - Gestionar todas las Comunicaciones con servicios externos que no sean de mensajeria instantanea (Gmail, Calendar).
    - Centralizar la lógica de envío y recepción de mensajes.
    - Manejar la disponibilidad y agendamiento de citas.
    - Proveer webhooks para integración con sistemas terceros.

Este módulo actúa como la capa de infraestructura/adaptación para canales de comunicación,
exponiendo entidades de dominio normalizadas (Appointment, etc.) al resto del sistema.
"""
