"""First Setup Procedure — meta-procedure for onboarding new tenants.

Chains: brand identity → positioning → first offer → first connection.
"""

from src.modules.copilot.application.procedures.base import Procedure, ProcedureStep

FIRST_SETUP = Procedure(
    procedure_id="first_setup",
    name="Configuración Inicial",
    description="Los 4 pasos esenciales para arrancar tu negocio en Nicolify.",
    steps=[
        ProcedureStep(
            step_id="brand_identity",
            module_id="brand",
            section_id="identity",
            instruction="Lo primero: ¿quién eres? Completa la identidad básica de tu marca.",
            validation="has_required_fields",
            tips=[
                "Si tienes un sitio web, puedo extraer tu información automáticamente",
            ],
            route_hint="brand-studio/esencia",
        ),
        ProcedureStep(
            step_id="brand_positioning",
            module_id="brand",
            section_id="positioning",
            instruction="Define tu propuesta de valor unica — por que te elegirian?",
            validation="has_required_fields",
            tips=[
                "Piensa en que te hace diferente de las alternativas del mercado",
            ],
            route_hint="brand-studio/estrategia",
        ),
        ProcedureStep(
            step_id="first_offer",
            module_id="offer",
            section_id=None,
            instruction="Crea tu primera oferta — el producto o servicio que quieres vender.",
            validation="has_any_data",
            tips=[
                "No necesita ser perfecta — la podrás editar después",
            ],
            route_hint="offer-studio",
        ),
        ProcedureStep(
            step_id="first_connection",
            module_id="connections",
            section_id=None,
            instruction="Conecta tu primer canal: Instagram, WhatsApp, o la plataforma donde hablas con tus clientes.",
            validation="has_any_data",
            tips=[
                "Instagram y WhatsApp son los canales más populares para empezar",
            ],
            route_hint="connections",
        ),
    ],
)
