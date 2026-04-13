"""Brand Setup Procedure — guides through all BrandSettings sections.

Steps correspond to BrandSettings.model_fields sections, validated
dynamically via schema_introspection (never hardcoded).
"""

from src.modules.copilot.application.procedures.base import Procedure, ProcedureStep

BRAND_SETUP = Procedure(
    procedure_id="brand_setup",
    name="Configuración de Marca",
    description=(
        "Configura tu identidad de marca paso a paso: identidad, historia,"
        " posicionamiento, narrativa, visuales y assets de comunicación."
    ),
    steps=[
        ProcedureStep(
            step_id="identity",
            module_id="brand",
            section_id="identity",
            instruction="Completa la identidad basica de tu marca: nombre, eslogan, mision, vision y valores.",
            validation="has_required_fields",
            tips=[
                "Si tienes un sitio web, puedo extraer esta informacion automaticamente",
                "Empieza por el nombre y eslogan — lo demas fluye desde ahi",
            ],
            route_hint="brand-studio/esencia",
        ),
        ProcedureStep(
            step_id="story",
            module_id="brand",
            section_id="story",
            instruction="Cuenta la historia de tu marca: origen, proposito y momentos clave.",
            validation="has_required_fields",
            tips=[
                "Una buena historia de marca conecta emocionalmente con tu audiencia",
                "Piensa en que problema te motivo a crear tu negocio",
            ],
            route_hint="brand-studio/esencia",
        ),
        ProcedureStep(
            step_id="positioning",
            module_id="brand",
            section_id="positioning",
            instruction=(
                "Define el posicionamiento de tu marca usando el framework Brand Love Key:"
                " UVP, atributos clave, beneficios funcionales y emocionales."
            ),
            validation="has_required_fields",
            tips=[
                "El posicionamiento responde: por que alguien te elegiria sobre la competencia?",
                "Puedo ayudarte a construir tu UVP basandome en tu identidad",
            ],
            route_hint="brand-studio/estrategia",
        ),
        ProcedureStep(
            step_id="narrative",
            module_id="brand",
            section_id="narrative",
            instruction="Construye tu narrativa con el framework StoryBrand: heroe, problema, guia y plan.",
            validation="has_required_fields",
            tips=[
                "En StoryBrand, tu cliente es el heroe, tu eres el guia",
                "El 'problema' tiene 3 niveles: externo, interno y filosofico",
            ],
            route_hint="brand-studio/estrategia",
        ),
        ProcedureStep(
            step_id="visuals",
            module_id="brand",
            section_id="visuals",
            instruction="Configura tu identidad visual: colores, tipografias, logo y estilo fotografico.",
            validation="has_required_fields",
            tips=[
                "Si tienes un sitio web, puedo extraer colores y tipografias automaticamente",
                "Elige colores que transmitan la personalidad de tu marca",
            ],
            route_hint="brand-studio/identidad-creativa",
        ),
        ProcedureStep(
            step_id="communication_assets",
            module_id="brand",
            section_id="communication_assets",
            instruction="Crea tus assets de comunicacion: voz de marca, tono, mensajes clave y pilares de contenido.",
            validation="has_required_fields",
            tips=[
                "La voz de marca debe ser consistente en todos los canales",
                "Define 3-5 pilares de contenido para guiar tu estrategia",
            ],
            route_hint="brand-studio/identidad-creativa",
        ),
    ],
)
