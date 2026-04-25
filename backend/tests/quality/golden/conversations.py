"""F9 — 20 canonical conversations across 8 categories.

Each entry is a (input, expected_output, category, brand_summary?) tuple.
The golden runner feeds them to ``CopilotJudge`` and asserts
``passes_threshold=True``.

The ``expected_output`` is the IDEAL response shape — what a 5/5 answer
should look like. The judge scores actual production output (or, in CI
default mode, a stubbed output that simulates a healthy response) against
the rubric, NOT the literal expected text. Semantic similarity, not exact
match.

Categories (F9 §4.1):
- url_contextual
- qa_simple
- qa_complex
- design_offer
- audit_funnel
- brand_setup
- multi_channel_synth
- error_recovery
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GoldenConversation:
    """One canonical conversation for regression detection."""

    id: str
    category: str
    user_input: str
    expected_output: str
    brand_summary: str | None = None
    context: str | None = None


_BRAND_VISIONARIAS = (
    "Marca: Visionarias. Voz cálida, cercana, motivacional. Hablamos a "
    "mujeres profesionales que buscan reinventarse. Posicionamiento: "
    "metodología propia para llevar talento a impacto monetizable."
)

_BRAND_CORAJE = (
    "Marca: MujeresCoraje. Voz directa, sin rodeos, empoderadora. "
    "Hablamos a emprendedoras latam que ya facturan pero quieren escalar. "
    "Posicionamiento: comunidad cerrada de validación + capital."
)


GOLDEN_CONVERSATIONS: tuple[GoldenConversation, ...] = (
    # ── 1. url_contextual ────────────────────────────────────────────────
    GoldenConversation(
        id="url_001_save_inspiration",
        category="url_contextual",
        user_input="Pego este link de competencia: https://mujerescoraje.com/programa",
        expected_output=(
            "Guardé la inspiración como `mujerescoraje-programa`. "
            "Detecté testimonios fuertes y CTA de cohorte cerrada. "
            "Puedes referenciarla en cualquier momento de la conversación."
        ),
        brand_summary=_BRAND_VISIONARIAS,
    ),
    GoldenConversation(
        id="url_002_recall_pinned",
        category="url_contextual",
        user_input="Rescata el bloque de testimonios de mujerescoraje que guardé antes",
        expected_output=(
            "De la inspiración `mujerescoraje-programa`: 3 testimonios en "
            "video con foco en transformación + 2 testimonios en texto con "
            "métricas de facturación. Estructura: hook · contexto · "
            "resultado. ¿Quieres que adapte ese formato a tu landing?"
        ),
        brand_summary=_BRAND_VISIONARIAS,
    ),
    # ── 2. qa_simple ─────────────────────────────────────────────────────
    GoldenConversation(
        id="qa_simple_001_lead_count",
        category="qa_simple",
        user_input="¿Cuántas personas escribieron esta semana?",
        expected_output=(
            "Recibiste 12 conversaciones inbound esta semana (lunes a hoy). "
            "8 son leads nuevos y 4 son retomas. ¿Quieres ver el breakdown "
            "por canal?"
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    GoldenConversation(
        id="qa_simple_002_active_offers",
        category="qa_simple",
        user_input="¿Qué ofertas tengo activas con descuento?",
        expected_output=(
            "Tienes 2 ofertas activas con descuento: "
            "1) `Cohorte Mayo` con 20% off (cierra el viernes), "
            "2) `Mentoría 1-1` con 15% off (rolling). "
            "Ambas en estado publicado."
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    GoldenConversation(
        id="qa_simple_003_brand_voice",
        category="qa_simple",
        user_input="Recordame mi voz de marca",
        expected_output=(
            "Tu voz es directa, sin rodeos, empoderadora. Hablás a "
            "emprendedoras que ya facturan y buscan escalar. Lo voy a "
            "respetar en cada propuesta."
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    # ── 3. qa_complex ────────────────────────────────────────────────────
    GoldenConversation(
        id="qa_complex_001_compare_offers",
        category="qa_complex",
        user_input=("¿Cuál de mis ofertas convierte mejor — Cohorte Mayo o Mentoría 1-1?"),
        expected_output=(
            "Cohorte Mayo: 8 conversaciones → 2 cierres (25% conversión). "
            "Mentoría 1-1: 5 conversaciones → 3 cierres (60% conversión). "
            "La Mentoría convierte mejor en 1-1, pero Cohorte trae más "
            "volumen. ¿Quieres explorar qué ajustar en Cohorte?"
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    GoldenConversation(
        id="qa_complex_002_funnel_drop",
        category="qa_complex",
        user_input="¿Dónde estoy perdiendo gente en el funnel?",
        expected_output=(
            "El drop más grande está entre captura (120 leads) y "
            "calificación (45 leads): pierdes el 62%. Probablemente el "
            "formulario de calificación tiene fricción. ¿Quieres que "
            "audite las preguntas?"
        ),
        brand_summary=_BRAND_VISIONARIAS,
    ),
    GoldenConversation(
        id="qa_complex_003_attribution",
        category="qa_complex",
        user_input="¿Qué canal me trae los leads más calificados?",
        expected_output=(
            "Instagram orgánico trae 40% del volumen pero solo 10% de "
            "cierres. Email nurture trae 20% del volumen y 50% de cierres. "
            "Recomiendo doblar nurture y simplificar el filtro de IG."
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    # ── 4. design_offer ──────────────────────────────────────────────────
    GoldenConversation(
        id="design_offer_001_from_url",
        category="design_offer",
        user_input=("Diseñame una oferta inspirada en https://hormozi.com/100m-offers"),
        expected_output=(
            "Analicé la página y detecté el patrón Grand Slam Offer: "
            "promesa específica + bonos + garantía + escasez. "
            "Antes de proponer, preguntale 2 cosas: "
            "1) ¿Qué resultado prometes en cuánto tiempo? "
            "2) ¿Con qué garantía respaldás? "
            "Con eso armo el value stack adaptado a tu marca."
        ),
        brand_summary=_BRAND_VISIONARIAS,
    ),
    GoldenConversation(
        id="design_offer_002_lead_magnet",
        category="design_offer",
        user_input="Necesito un lead magnet para mi cohorte",
        expected_output=(
            "Para una cohorte, el lead magnet ideal es un asset que "
            "demuestre tu metodología en pequeño. Propongo: 'Auditoría "
            "express en 10 minutos' (PDF + checklist) — cualifica + da "
            "valor + abre puerta a oferta. ¿Te sirve esa dirección o "
            "preferís algo más educativo?"
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    # ── 5. audit_funnel ──────────────────────────────────────────────────
    GoldenConversation(
        id="audit_funnel_001_captura",
        category="audit_funnel",
        user_input="Audita mi etapa de captura",
        expected_output=(
            "Etapa de captura — diagnóstico:\n"
            "1. Volumen: 120 leads/semana (saludable).\n"
            "2. Fuentes: 80% IG orgánico, 15% referido, 5% pago.\n"
            "3. Bottleneck: el copy del CTA en bio dice 'aprende más' "
            "(genérico). Cámbialo por algo específico de la promesa.\n"
            "Próximo paso sugerido: A/B testing del CTA."
        ),
        brand_summary=_BRAND_VISIONARIAS,
    ),
    GoldenConversation(
        id="audit_funnel_002_nutricion",
        category="audit_funnel",
        user_input="¿Cómo está mi etapa de nutrición?",
        expected_output=(
            "Nutrición: tienes una secuencia de 4 emails con open rate "
            "promedio de 38% (saludable) pero CTR de 2% (bajo). "
            "El problema está en los CTA — son débiles. "
            "Recomiendo: agregar un email con caso de éxito + CTA "
            "claro a la oferta principal."
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    # ── 6. brand_setup ───────────────────────────────────────────────────
    GoldenConversation(
        id="brand_setup_001_voice_capture",
        category="brand_setup",
        user_input=("Estoy armando mi marca desde cero. Soy coach de mujeres profesionales en transición."),
        expected_output=(
            "Vamos paso a paso. Para capturar tu voz necesito 3 cosas:\n"
            "1. ¿Qué transformación específica generas? "
            "(de X a Y en cuánto tiempo)\n"
            "2. ¿Cómo le hablarías a tu cliente ideal en un mensaje "
            "directo? (formal/cercano/directo)\n"
            "3. ¿Qué NO sos? (para definir bordes claros)\n"
            "Empieza por la #1 cuando puedas."
        ),
        brand_summary=None,
    ),
    GoldenConversation(
        id="brand_setup_002_positioning",
        category="brand_setup",
        user_input="No sé cómo posicionarme — hago lo mismo que muchos otros",
        expected_output=(
            "Esa es la pregunta correcta. Posicionamiento no es 'qué "
            "hago' sino 'para quién + qué problema específico + qué hago "
            "distinto'. ¿Te animas a responder eso para tu caso? "
            "Te voy guiando con preguntas si lo necesitas."
        ),
        brand_summary=None,
    ),
    # ── 7. multi_channel_synth ───────────────────────────────────────────
    GoldenConversation(
        id="multi_channel_001_whatsapp",
        category="multi_channel_synth",
        user_input=("Dame el resumen del programa Cohorte Mayo para WhatsApp"),
        expected_output=(
            "Cohorte Mayo · 8 semanas\n\n"
            "Para emprendedoras que ya facturan y quieren escalar a "
            "consultoría premium.\n\n"
            "✅ 8 sesiones grupales en vivo\n"
            "✅ 1-1 mensual con mentora\n"
            "✅ Comunidad privada de validación\n\n"
            "Cierre 31 mayo · 12 cupos · 20% off hasta el viernes\n"
            "👉 https://link.al/cohorte-mayo"
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    GoldenConversation(
        id="multi_channel_002_email",
        category="multi_channel_synth",
        user_input=(
            "Adapta esto para un email a cold list: 'Tenemos cohorte "
            "abriendo en mayo, son 8 semanas de mentoría grupal'"
        ),
        expected_output=(
            "Asunto: ¿Lista para escalar tu negocio en 8 semanas?\n\n"
            "Hola,\n\n"
            "El próximo 6 de mayo abrimos Cohorte Mayo. 8 semanas de "
            "mentoría grupal pensada para emprendedoras que ya facturan "
            "pero sienten que llegaron a un techo.\n\n"
            "Trabajamos juntas: estrategia, oferta, equipo y mindset.\n\n"
            "Si quieres conocer detalles, respóndeme este mail y te paso "
            "la página completa.\n\n"
            "Un abrazo,\n"
            "[Tu nombre]"
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    # ── 8. error_recovery ────────────────────────────────────────────────
    GoldenConversation(
        id="error_recovery_001_no_data",
        category="error_recovery",
        user_input="¿Cuántos leads tengo este mes?",
        expected_output=(
            "No encontré datos de leads para este mes. Puede ser que la "
            "integración con Manychat no esté sincronizando — revisemos "
            "en Conexiones. Mientras tanto, ¿quieres ver leads del mes "
            "pasado para comparar?"
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    GoldenConversation(
        id="error_recovery_002_ambiguous",
        category="error_recovery",
        user_input="Mejorá la oferta",
        expected_output=(
            "Necesito más contexto para ayudarte mejor. Tienes 2 ofertas "
            "activas: Cohorte Mayo y Mentoría 1-1. ¿Cuál quieres mejorar? "
            "Y ¿qué parte: precio, copy, bonos, urgencia? "
            "Dime cuál y arrancamos."
        ),
        brand_summary=_BRAND_CORAJE,
    ),
    GoldenConversation(
        id="multi_channel_003_sms",
        category="multi_channel_synth",
        user_input=("Hazme la versión SMS de: 'Cohorte Mayo cierra el viernes con 20% off, 12 cupos disponibles'"),
        expected_output=("Cohorte Mayo cierra viernes. 20% off · 12 cupos. Inscripción: link.al/cm"),
        brand_summary=_BRAND_CORAJE,
    ),
    GoldenConversation(
        id="error_recovery_003_off_topic",
        category="error_recovery",
        user_input="¿Cuál es la capital de Francia?",
        expected_output=(
            "Esa pregunta queda fuera del scope que puedo ayudarte. "
            "Estoy enfocada en marketing, ofertas, marca y datos de tu "
            "negocio. ¿Hay algo en alguna de esas áreas que pueda "
            "trabajar contigo?"
        ),
        brand_summary=_BRAND_VISIONARIAS,
    ),
)


CATEGORIES: tuple[str, ...] = (
    "url_contextual",
    "qa_simple",
    "qa_complex",
    "design_offer",
    "audit_funnel",
    "brand_setup",
    "multi_channel_synth",
    "error_recovery",
)


__all__ = ("CATEGORIES", "GOLDEN_CONVERSATIONS", "GoldenConversation")
