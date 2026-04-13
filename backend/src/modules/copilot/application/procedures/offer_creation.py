"""Offer Creation Procedure — guides through creating and configuring an offer.

Uses has_any_data validation since Offer is a SQLAlchemy model (no single Pydantic root).
"""

from src.modules.copilot.application.procedures.base import Procedure, ProcedureStep

OFFER_CREATION = Procedure(
    procedure_id="offer_creation",
    name="Creación de Oferta",
    description="Crea y configura tu primera oferta: producto/servicio, precio, avatar, objeciones y knowledge base.",
    steps=[
        ProcedureStep(
            step_id="create_offer",
            module_id="offer",
            section_id=None,
            instruction="Crea al menos una oferta con nombre, descripción y precio.",
            validation="has_any_data",
            tips=[
                "Empieza por tu oferta principal — la que más vendes o quieres vender",
                "Puedo ayudarte a definir el precio basándome en tu mercado",
            ],
            route_hint="offer-studio",
        ),
    ],
)
