"""S10 — 20 sales_agent goldens cubriendo 6 categorías.

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Cada entrada es una conversación canónica (input lead + ASSISTANT_OUTPUT
ideal). Fixtures sintéticas — **NUNCA PII real**. El judge evalúa la
respuesta ideal contra la rúbrica para verificar el plumbing; la versión
real (RUN_LLM_JUDGE=1 + cron weekly) compara la respuesta real del agente
contra la rúbrica.

Categorías (S10 §criterios de éxito):

- ``qualification`` — rapport → discovery (lead llega frío, agente
  califica con preguntas neutras).
- ``objections`` — manejo de objeciones (precio, tiempo, validación).
- ``closing_payment`` — cierre + payment link (lead listo para comprar).
- ``booking`` — booking link (lead pide demo / llamada).
- ``multi_channel`` — formato canal-específico (whatsapp/telegram/ig/web/sms/email).
- ``brand_voice_diff`` — diferenciación tenant A vs B con mismo input
  (cache invariance test).

Total: 20 entries. Brand voices y data sintética.
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIES: tuple[str, ...] = (
    "brand_voice_diff",
    "booking",
    "closing_payment",
    "multi_channel",
    "objections",
    "qualification",
)


@dataclass(frozen=True, slots=True)
class SalesAgentGolden:
    """One canonical sales conversation for regression detection."""

    id: str
    category: str
    user_input: str
    expected_output: str
    brand_voice: str
    channel: str
    stage: str
    context: str | None = None


# ── Brand voices sintéticas (no PII real) ────────────────────────────────
_BRAND_FORMAL = (
    "Marca: Visionarias. Voz cálida y profesional, español neutro LATAM (sin"
    " voseo). Siempre tutea. Habla a mujeres profesionales que buscan"
    " reinventarse. Posicionamiento: metodología validada para llevar"
    " talento a impacto monetizable. Tono: claro, motivacional sin"
    " hipérbole. Sin emojis innecesarios."
)

_BRAND_CASUAL_AR = (
    "Marca: BrazaLAB. Voz cercana, voseo argentino (vos / tenés / podés)"
    " explícitamente configurado por el tenant — feature, no bug."
    " Habla a emprendedoras LATAM. Tono: directo, sin rodeos, con humor"
    " sutil. Usa emojis con moderación en canales async (whatsapp,"
    " telegram). Nunca tutea."
)

_BRAND_MINIMAL = (
    "Marca: Atlas Studio. Voz minimalista, frases cortas, español neutro."
    " Habla a operadores B2B. Tono: directo, sin adornos. Cero emojis."
    " Markdown plano. Nunca preguntas retóricas."
)

# ── Goldens (20 total) ───────────────────────────────────────────────────
GOLDEN_CONVERSATIONS: tuple[SalesAgentGolden, ...] = (
    # ── 1. qualification (rapport→discovery) — 3 entries ──────────────────
    SalesAgentGolden(
        id="qual_001_cold_inbound",
        category="qualification",
        user_input="hola, vi tu reel y me llamó la atención",
        expected_output=(
            "¡Qué bueno que escribiste! Para entenderte mejor, contame"
            " brevemente: ¿qué te resonó del reel y cuál es el reto que"
            " hoy más te frena?"
        ),
        brand_voice=_BRAND_FORMAL,
        channel="instagram_dm",
        stage="rapport",
    ),
    SalesAgentGolden(
        id="qual_002_returning_user_continuity",
        category="qualification",
        user_input="hola de nuevo, estaba pensando en lo que hablamos la semana pasada",
        expected_output=(
            "Hola, qué gusto leerte otra vez. La última vez quedaste con"
            " la duda sobre tiempo de dedicación. ¿Querés retomar desde"
            " ahí o cambió algo en estas semanas?"
        ),
        brand_voice=_BRAND_CASUAL_AR,
        channel="whatsapp",
        stage="rapport",
        context="last_session_summary: lead preguntó por tiempo de dedicación, no avanzó al cierre.",
    ),
    SalesAgentGolden(
        id="qual_003_discovery_budget",
        category="qualification",
        user_input="me interesa pero todavía no sé bien si me sirve",
        expected_output=(
            "Tiene total sentido tomarse el tiempo. Para ayudarte a"
            " decidir, dos preguntas: ¿qué resultado querés tener en"
            " 90 días, y qué inversión tenés disponible este trimestre?"
        ),
        brand_voice=_BRAND_FORMAL,
        channel="web_chat",
        stage="discovery",
    ),
    # ── 2. objections — 3 entries ─────────────────────────────────────────
    SalesAgentGolden(
        id="obj_001_price",
        category="objections",
        user_input="me parece caro la verdad, no sé si lo vale",
        expected_output=(
            "Te entiendo, es una decisión importante. Mirá, la inversión"
            " se justifica cuando el resultado es claro: en cohortes"
            " anteriores el promedio recuperó la inversión en los"
            " primeros 90 días. ¿Querés que te muestre 2 casos similares"
            " al tuyo para que decidas con data?"
        ),
        brand_voice=_BRAND_CASUAL_AR,
        channel="whatsapp",
        stage="presentation",
    ),
    SalesAgentGolden(
        id="obj_002_no_time",
        category="objections",
        user_input="no tengo tiempo ahora, estoy a full",
        expected_output=(
            "Entiendo, el tiempo es lo más finito. El programa está"
            " diseñado para 4 horas semanales, asincrónico. ¿Te encaja"
            " si lo encarás los fines de semana, o preferís esperar al"
            " próximo trimestre?"
        ),
        brand_voice=_BRAND_FORMAL,
        channel="web_chat",
        stage="presentation",
    ),
    SalesAgentGolden(
        id="obj_003_validation_needed",
        category="objections",
        user_input="quiero pensarlo y consultarlo con mi pareja",
        expected_output=(
            "Es una decisión que vale la pena conversar. Para que vayas"
            " con argumentos claros, te paso los 3 casos cercanos a tu"
            " contexto + el plan semana a semana. ¿Te llegan por acá o"
            " preferís email?"
        ),
        brand_voice=_BRAND_FORMAL,
        channel="instagram_dm",
        stage="presentation",
    ),
    # ── 3. closing + payment link — 2 entries ─────────────────────────────
    SalesAgentGolden(
        id="close_001_payment_link",
        category="closing_payment",
        user_input="ok dale, mandame el link",
        expected_output=(
            "Genial, te paso el link de pago seguro:"
            " https://pago.test/checkout/abc123. Una vez que confirmes,"
            " te llega el acceso por mail en menos de 5 minutos."
            " ¿Cualquier cosa, te aviso por acá?"
        ),
        brand_voice=_BRAND_CASUAL_AR,
        channel="whatsapp",
        stage="closing",
    ),
    SalesAgentGolden(
        id="close_002_payment_confirmed",
        category="closing_payment",
        user_input="ya pagué, ¿cuándo me llega?",
        expected_output=(
            "Confirmado, ya tengo registrado tu pago. Te acabo de enviar"
            " a tu correo el acceso a la cohorte y la invitación al"
            " kickoff del lunes. Si no llega en 5 minutos, decime y lo"
            " reenvío."
        ),
        brand_voice=_BRAND_FORMAL,
        channel="whatsapp",
        stage="closing",
    ),
    # ── 4. booking link — 2 entries ───────────────────────────────────────
    SalesAgentGolden(
        id="book_001_demo_request",
        category="booking",
        user_input="me podrías agendar una llamada para esta semana?",
        expected_output=(
            "Claro. Te paso el link para reservar el horario que te"
            " convenga: https://book.test/demo/lead-001."
            " Confirmá y te llega un recordatorio 24 horas antes."
        ),
        brand_voice=_BRAND_FORMAL,
        channel="instagram_dm",
        stage="discovery",
    ),
    SalesAgentGolden(
        id="book_002_reschedule",
        category="booking",
        user_input="no voy a poder mañana, podemos mover la llamada?",
        expected_output=(
            "Sin problema. Te paso de nuevo el link para que elijas otro"
            " horario que te encaje:"
            " https://book.test/demo/lead-001-rescheduled. Cuando"
            " confirmes, te llega el recordatorio."
        ),
        brand_voice=_BRAND_FORMAL,
        channel="whatsapp",
        stage="presentation",
    ),
    # ── 5. multi-channel format — 6 entries (uno por canal) ───────────────
    SalesAgentGolden(
        id="chan_001_whatsapp_short",
        category="multi_channel",
        user_input="hola",
        expected_output=("¡Hola! Gracias por escribir. ¿En qué te puedo ayudar hoy?"),
        brand_voice=_BRAND_FORMAL,
        channel="whatsapp",
        stage="rapport",
    ),
    SalesAgentGolden(
        id="chan_002_telegram_async",
        category="multi_channel",
        user_input="info del programa",
        expected_output=(
            "Te resumo en 3 puntos:\n\n"
            "1. Cohorte de 8 semanas, 4 hs/semana asincrónicas.\n"
            "2. Mentoría grupal + acceso al community.\n"
            "3. Garantía de avance por hitos.\n\n"
            "¿Cuál te gustaría profundizar primero?"
        ),
        brand_voice=_BRAND_FORMAL,
        channel="telegram",
        stage="discovery",
    ),
    SalesAgentGolden(
        id="chan_003_ig_dm_emoji_ok",
        category="multi_channel",
        user_input="me lo comentás un poco?",
        expected_output=(
            "¡Dale! ✨ Es un programa de 8 semanas pensado para que pases"
            " de tener la idea a tener clientes pagando. Te puedo contar"
            " más por acá o te paso un link para reservar 15 minutos."
            " ¿Qué preferís?"
        ),
        brand_voice=_BRAND_CASUAL_AR,
        channel="instagram_dm",
        stage="discovery",
    ),
    SalesAgentGolden(
        id="chan_004_web_chat_markdown",
        category="multi_channel",
        user_input="¿cuál es el plan de pagos?",
        expected_output=(
            "Tenemos 3 opciones flexibles:\n\n"
            "- **Pago único** con 15% de descuento.\n"
            "- **3 cuotas** sin recargo.\n"
            "- **6 cuotas** con un pequeño recargo financiero.\n\n"
            "¿Cuál te encaja mejor para empezar?"
        ),
        brand_voice=_BRAND_FORMAL,
        channel="web_chat",
        stage="presentation",
    ),
    SalesAgentGolden(
        id="chan_005_sms_no_markdown",
        category="multi_channel",
        user_input="info corta del precio",
        expected_output=(
            "Programa 8 semanas, USD 480 pago único o 3 cuotas sin recargo. ¿Te paso el link para reservar?"
        ),
        brand_voice=_BRAND_MINIMAL,
        channel="sms",
        stage="presentation",
    ),
    SalesAgentGolden(
        id="chan_006_email_formal",
        category="multi_channel",
        user_input="me podrías enviar la propuesta por escrito?",
        expected_output=(
            "Hola, gracias por tu interés. Te comparto la propuesta:\n\n"
            "1. Programa de 8 semanas, modalidad asincrónica.\n"
            "2. Inversión: USD 480 (pago único) o 3 cuotas sin recargo.\n"
            "3. Incluye mentoría grupal y acceso al community.\n\n"
            "Si querés avanzar, respondé este correo y te envío el"
            " enlace de pago seguro. Saludos."
        ),
        brand_voice=_BRAND_FORMAL,
        channel="email",
        stage="presentation",
    ),
    # ── 6. brand voice diff (tenant A vs B) — 4 entries (2 pares) ─────────
    SalesAgentGolden(
        id="voice_001_formal_response",
        category="brand_voice_diff",
        user_input="¿cómo es el programa?",
        expected_output=(
            "Es un programa de 8 semanas con metodología validada,"
            " mentoría grupal y avance por hitos. ¿Querés que te"
            " comparta los 3 resultados típicos al cierre?"
        ),
        brand_voice=_BRAND_FORMAL,
        channel="web_chat",
        stage="discovery",
    ),
    SalesAgentGolden(
        id="voice_002_casual_ar_response",
        category="brand_voice_diff",
        user_input="¿cómo es el programa?",
        expected_output=(
            "Mirá, son 8 semanas, 4 horas por semana — fácil de bancar"
            " si tenés laburo. Te lleva de la idea a tener gente pagando."
            " ¿Querés que te tire los 3 casos parecidos al tuyo?"
        ),
        brand_voice=_BRAND_CASUAL_AR,
        channel="web_chat",
        stage="discovery",
    ),
    SalesAgentGolden(
        id="voice_003_minimal_response",
        category="brand_voice_diff",
        user_input="¿cuánto sale?",
        expected_output=("USD 480. Pago único o 3 cuotas. ¿Avanzamos?"),
        brand_voice=_BRAND_MINIMAL,
        channel="web_chat",
        stage="presentation",
    ),
    SalesAgentGolden(
        id="voice_004_formal_pricing_response",
        category="brand_voice_diff",
        user_input="¿cuánto sale?",
        expected_output=(
            "La inversión es de USD 480 con dos opciones de pago: único"
            " con 15% de descuento o 3 cuotas sin recargo. ¿Cuál te"
            " encaja mejor para arrancar?"
        ),
        brand_voice=_BRAND_FORMAL,
        channel="web_chat",
        stage="presentation",
    ),
)


__all__ = (
    "CATEGORIES",
    "GOLDEN_CONVERSATIONS",
    "SalesAgentGolden",
)
