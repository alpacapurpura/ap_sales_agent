"""add ad_offer_associations and ad_campaign_templates tables

Revision ID: 039_add_ad_offer_assoc
Revises: 038_add_launch_editions
Create Date: 2026-04-10 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "039_add_ad_offer_assoc"
down_revision: str | None = "038_add_launch_editions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- ad_offer_associations --------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_offer_associations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            target_type VARCHAR(20) NOT NULL,
            target_external_id VARCHAR(255) NOT NULL,
            offer_id UUID,
            association_type VARCHAR(50) NOT NULL,
            confidence VARCHAR(20),
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ad_offer_associations_tenant_id
        ON ad_offer_associations (tenant_id)
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_ad_offer_tenant_target
        ON ad_offer_associations (tenant_id, target_type, target_external_id)
        WHERE deleted_at IS NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ad_offer_tenant_offer
        ON ad_offer_associations (tenant_id, offer_id)
    """)

    # --- ad_campaign_templates --------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_campaign_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            offer_archetype VARCHAR(50) NOT NULL,
            offer_onboarding_action VARCHAR(50),
            offer_is_lead_magnet BOOLEAN,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            recommended_objective VARCHAR(50) NOT NULL,
            recommended_optimization_goal VARCHAR(100),
            recommended_destination_type VARCHAR(100),
            structure_hints JSONB DEFAULT '{}'::jsonb,
            priority INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
    """)

    # Seed 8 templates. Idempotent via NOT EXISTS guard keyed on the
    # (archetype, onboarding_action, is_lead_magnet) triplet.
    seed_rows = [
        (
            "PRODUCTO",
            None,
            True,
            "Lead Magnet - Captar emails",
            "Lead magnet: captá emails con formulario o página de descarga",
            "OUTCOME_LEADS",
            "LEAD_GENERATION",
            "ON_AD",
            100,
        ),
        (
            "PRODUCTO",
            None,
            False,
            "Producto Digital - Venta directa",
            "Producto digital con checkout web: optimizá para compras directas",
            "OUTCOME_SALES",
            "OFFSITE_CONVERSIONS",
            "WEBSITE",
            100,
        ),
        (
            "PROGRAMA",
            None,
            False,
            "Programa/Curso - Checkout directo",
            "Curso/cohort: checkout directo o VSL con CTA de compra",
            "OUTCOME_SALES",
            "OFFSITE_CONVERSIONS",
            "WEBSITE",
            100,
        ),
        (
            "SERVICIO",
            "BOOK_KICKOFF_CALL",
            False,
            "Servicio 1:1 - Mensajes para agendar",
            "Servicio 1:1: usá WhatsApp/Messenger para calificar y agendar",
            "OUTCOME_MESSAGES",
            "CONVERSATIONS",
            "MESSENGER",
            100,
        ),
        (
            "SERVICIO",
            "FILL_INTAKE_FORM",
            False,
            "Servicio con formulario - Lead Forms",
            "Servicio con formulario: Lead Forms de Meta",
            "OUTCOME_LEADS",
            "LEAD_GENERATION",
            "ON_AD",
            100,
        ),
        (
            "MEMBRESIA",
            "JOIN_COMMUNITY",
            False,
            "Membresía paga - Suscripción",
            "Membresía: optimizá para suscripción vía checkout",
            "OUTCOME_SALES",
            "OFFSITE_CONVERSIONS",
            "WEBSITE",
            100,
        ),
        (
            "MEMBRESIA",
            "INSTANT_ACCESS_EMAIL",
            False,
            "Comunidad gratuita - Lead capture",
            "Comunidad gratuita: lead capture",
            "OUTCOME_LEADS",
            "LEAD_GENERATION",
            "ON_AD",
            100,
        ),
        (
            "EXPERIENCIA",
            None,
            False,
            "Experiencia/Evento - Venta de boleto",
            "Evento/retreat: compra de boleto o reserva",
            "OUTCOME_SALES",
            "OFFSITE_CONVERSIONS",
            "WEBSITE",
            100,
        ),
    ]

    insert_sql = """
        INSERT INTO ad_campaign_templates (
            offer_archetype,
            offer_onboarding_action,
            offer_is_lead_magnet,
            name,
            description,
            recommended_objective,
            recommended_optimization_goal,
            recommended_destination_type,
            priority
        )
        SELECT
            :archetype, :onboarding, :is_lead,
            :name, :descr, :obj, :optg, :dest, :prio
        WHERE NOT EXISTS (
            SELECT 1 FROM ad_campaign_templates
            WHERE offer_archetype = :archetype
              AND COALESCE(offer_onboarding_action, '')
                  = COALESCE(CAST(:onboarding AS VARCHAR), '')
              AND COALESCE(offer_is_lead_magnet::text, '')
                  = COALESCE(CAST(:is_lead AS BOOLEAN)::text, '')
        )
    """
    from sqlalchemy import text as _sa_text

    bind = op.get_bind()
    for row in seed_rows:
        bind.execute(
            _sa_text(insert_sql),
            {
                "archetype": row[0],
                "onboarding": row[1],
                "is_lead": row[2],
                "name": row[3],
                "descr": row[4],
                "obj": row[5],
                "optg": row[6],
                "dest": row[7],
                "prio": row[8],
            },
        )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ad_offer_tenant_offer")
    op.execute("DROP INDEX IF EXISTS ix_ad_offer_tenant_target")
    op.execute("DROP INDEX IF EXISTS ix_ad_offer_associations_tenant_id")
    op.execute("DROP TABLE IF EXISTS ad_offer_associations")
    op.execute("DROP TABLE IF EXISTS ad_campaign_templates")
