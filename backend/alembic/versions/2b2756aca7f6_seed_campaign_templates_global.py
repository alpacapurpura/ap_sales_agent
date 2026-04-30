"""seed campaign templates global

Revision ID: 2b2756aca7f6
Revises: 112_campaigns_domain
Create Date: 2026-04-30 07:36:14.214680

Seeds 5 global campaign templates (tenant_id IS NULL) using uuid_generate_v5 for
deterministic, idempotent IDs. ON CONFLICT (id) DO NOTHING ensures re-running is safe.

Templates:
1. welcome          — 3-step welcome drip (email_drip)
2. launch-4day      — 4-step product launch sequence (email_drip)
3. webinar          — 3-step webinar invite + reminder (event_trigger)
4. cold-reactivation— 2-step re-engagement (email_broadcast)
5. post-purchase    — 3-step post-purchase nurture (email_drip)
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2b2756aca7f6"
down_revision: str | None = "112_campaigns_domain"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Namespace UUID for campaign template seeds — deterministic across envs.
# uuid5(DNS, "nicolify.campaigns.global_templates") — precomputed constant.
_NS = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"  # uuid.NAMESPACE_DNS


def upgrade() -> None:
    """Insert 5 global campaign templates. Idempotent via ON CONFLICT DO NOTHING."""
    op.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    """)

    op.execute(f"""
        INSERT INTO campaign_template (
            id, tenant_id, slug, name, description,
            campaign_type, template_body,
            recommended_segment_slugs, tags,
            version, created_at, updated_at
        )
        VALUES
        -- 1. Welcome drip — 3 steps
        (
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.welcome'),
            NULL,
            'welcome',
            'Bienvenida (3 pasos)',
            'Secuencia de bienvenida automatizada para nuevos suscriptores. '
            'Presenta la marca, el método y una oferta de bajo compromiso.',
            'email_drip',
            '{{"steps": ['
                '{{"step_index": 0, "step_type": "send_message", "label": "Bienvenida", '
                '"config": {{"subject": "¡Bienvenido/a! Así te ayudamos", "delay_hours": 0}}}},'
                '{{"step_index": 1, "step_type": "wait_delay", "label": "Espera 1 día", '
                '"config": {{"delay_hours": 24}}}},'
                '{{"step_index": 2, "step_type": "send_message", "label": "Tu primer recurso", '
                '"config": {{"subject": "El recurso que más te va a ayudar"}}}}]}}',
            '["new_subscribers", "all_leads"]',
            '["onboarding", "bienvenida", "nurture"]',
            1,
            NOW(), NOW()
        ),

        -- 2. Launch 4-day — 4 steps
        (
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.launch-4day'),
            NULL,
            'launch-4day',
            'Lanzamiento 4 días',
            'Secuencia de lanzamiento de 4 emails para introducir y vender una oferta nueva. '
            'Genera expectativa, presenta el problema, ofrece la solución y cierra con urgencia.',
            'email_drip',
            '{{"steps": ['
                '{{"step_index": 0, "step_type": "send_message", "label": "Día 1 — Teaser", '
                '"config": {{"subject": "Algo importante está por llegar…", "delay_hours": 0}}}},'
                '{{"step_index": 1, "step_type": "send_message", "label": "Día 2 — El problema", '
                '"config": {{"subject": "¿Cuánto te cuesta este problema hoy?", "delay_hours": 24}}}},'
                '{{"step_index": 2, "step_type": "send_message", "label": "Día 3 — La solución", '
                '"config": {{"subject": "Presentamos [Oferta]: la solución que buscabas", "delay_hours": 48}}}},'
                '{{"step_index": 3, "step_type": "send_message", "label": "Día 4 — Urgencia", '
                '"config": {{"subject": "Últimas horas: precio especial solo hoy", "delay_hours": 72}}}}]}}',
            '["warm_leads", "subscribers"]',
            '["lanzamiento", "venta", "oferta"]',
            1,
            NOW(), NOW()
        ),

        -- 3. Webinar — 3 steps
        (
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.webinar'),
            NULL,
            'webinar',
            'Webinar (invitación + recordatorio)',
            'Secuencia de 3 mensajes para invitar a un webinar, confirmar el registro '
            'y enviar un recordatorio 1 hora antes del evento.',
            'event_trigger',
            '{{"steps": ['
                '{{"step_index": 0, "step_type": "send_message", "label": "Invitación", '
                '"config": {{"subject": "Te invito a mi webinar gratuito", "delay_hours": 0}}}},'
                '{{"step_index": 1, "step_type": "send_message", "label": "Confirmación", '
                '"config": {{"subject": "Registro confirmado — guarda la fecha", "delay_hours": 1}}}},'
                '{{"step_index": 2, "step_type": "send_message", "label": "Recordatorio -1h", '
                '"config": {{"subject": "¡Empezamos en 1 hora! Aquí el link", "delay_hours": -1, '
                '"relative_to": "event_start"}}}}]}}',
            '["subscribers", "warm_leads"]',
            '["webinar", "evento", "invitacion"]',
            1,
            NOW(), NOW()
        ),

        -- 4. Cold reactivation — 2 steps
        (
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.cold-reactivation'),
            NULL,
            'cold-reactivation',
            'Reactivación leads fríos',
            'Secuencia de 2 mensajes para re-enganchar leads que llevan más de 60 días sin actividad. '
            'Pregunta directa + oferta de valor sin costo.',
            'email_broadcast',
            '{{"steps": ['
                '{{"step_index": 0, "step_type": "send_message", "label": "Ping de reactivación", '
                '"config": {{"subject": "¿Sigues interesado/a en [tema]?", "delay_hours": 0}}}},'
                '{{"step_index": 1, "step_type": "send_message", "label": "Regalo de reactivación", '
                '"config": {{"subject": "Un recurso gratuito para ti (sin compromisos)", "delay_hours": 48}}}}]}}',
            '["cold_leads", "inactive_60d"]',
            '["reactivacion", "frios", "nurture"]',
            1,
            NOW(), NOW()
        ),

        -- 5. Post-purchase — 3 steps
        (
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.post-purchase'),
            NULL,
            'post-purchase',
            'Post-compra (3 pasos)',
            'Secuencia de 3 mensajes para onboardear al cliente recién comprado, garantizar activación '
            'y solicitar testimonio en el momento de mayor satisfacción.',
            'email_drip',
            '{{"steps": ['
                '{{"step_index": 0, "step_type": "send_message", "label": "Bienvenida cliente", '
                '"config": {{"subject": "¡Gracias por tu compra! Empieza aquí", "delay_hours": 0}}}},'
                '{{"step_index": 1, "step_type": "send_message", "label": "Check-in día 3", '
                '"config": {{"subject": "¿Cómo va todo? ¿Necesitas ayuda?", "delay_hours": 72}}}},'
                '{{"step_index": 2, "step_type": "send_message", "label": "Solicitud testimonio", '
                '"config": {{"subject": "Tu opinión nos importa — 2 minutos", "delay_hours": 168}}}}]}}',
            '["customers", "new_buyers"]',
            '["post-compra", "onboarding", "testimonios"]',
            1,
            NOW(), NOW()
        )
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove the 5 seeded global templates by their deterministic IDs."""
    op.execute(f"""
        DELETE FROM campaign_template
        WHERE id IN (
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.welcome'),
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.launch-4day'),
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.webinar'),
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.cold-reactivation'),
            uuid_generate_v5('{_NS}'::uuid, 'nicolify.template.post-purchase')
        )
        AND tenant_id IS NULL;
    """)
