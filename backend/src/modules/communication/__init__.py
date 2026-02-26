"""
Módulo de Comunicación y Canales Externos.

Responsabilidad:
    - Gestionar todas las conexiones con servicios externos (WhatsApp, Telegram, Gmail, Calendar).
    - Centralizar la lógica de envío y recepción de mensajes.
    - Manejar la disponibilidad y agendamiento de citas.
    - Proveer webhooks para integración con sistemas terceros.

Este módulo actúa como la capa de infraestructura/adaptación para canales de comunicación,
exponiendo entidades de dominio normalizadas (Message, Appointment) al resto del sistema.
"""
