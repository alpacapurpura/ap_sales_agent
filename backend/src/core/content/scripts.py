from typing import Dict, Any

# Script Registry - Centralized Content Management
# Based on: FUNNEL ESTRATÉGICO DE VISIONARIAS LATAM-2.docx

SCRIPTS_REGISTRY: Dict[str, Dict[str, Any]] = {
    # --- OBJECTIONS & FAQS ---
    "faq_program_details": {
        "text": """Visionarias es un programa anual de transformación interna + liderazgo + estrategia.
Incluye:
- Mentorías grupales con Ileana.
- Acompañamiento emocional + energético con Camila.
- Módulos completos de claridad, liderazgo, ventas, propósito, bienestar, finanzas y orden.
- Rituales, dinámicas y ejercicios profundos.
- Comunidad íntima y segura.
Es una transformación integral, no un curso aislado."""
    },
    "faq_who_is_it_for": {
        "text": """Para este programa es importante que tengas un negocio activo, que ya esté generando ventas, o como mínimo que tengas una idea de negocio clara.
Si aún no tienes claridad de tu negocio, este programa no es para ti por ahora (más adelante lanzaremos algo para esa etapa)."""
    },
    "faq_time_commitment": {
        "text": """Este es un programa INTENSIVO, el requerimiento mínimo son 4 horas semanales.
- Sesiones en vivo: Martes y Jueves de 8:30am a 10:30am.
- Ejercicios diarios: 15 minutos.
Todo queda grabado por un año si no puedes asistir en vivo."""
    },
    "faq_dates": {
        "text": "Empezamos el 10 de Febrero 2026."
    },
    "faq_price_payment": {
        "text": """Inversión: S/. 4,444 (Oferta de Preventa) o S/. 5,925 (Regular).
Formas de pago:
1. Tarjeta de Crédito: Hasta 6 cuotas SIN intereses.
2. Débito / Transferencia / Yape.
¿Te gustaría que te envíe el link de pago?"""
    },
    "faq_guarantee": {
        "text": """El miedo es normal. Por eso tienes nuestra Garantía de Satisfacción de 7 días.
Entras, pruebas la primera semana (desde el 10 de Febrero) y si no es para ti, te devolvemos el 100%. El riesgo es mío."""
    },
    "faq_online_format": {
        "text": "Es 100% online para que puedas transformarte desde cualquier lugar. Tendremos un encuentro presencial opcional para conectar en comunidad."
    },
    "faq_spirituality": {
        "text": "No necesitas ser 'espiritual'. Visionarias combina lo emocional, mental, energético, práctico y estratégico. Es integral, no místico."
    },
    
    # --- OBJECTION HANDLING STRATEGIES ---
    "obj_price": {
        "strategy": "ROI Reframing",
        "script": """Te entiendo, es una inversión importante.
Pero piénsalo así: Si lo divides en 6 meses, son S/. 24 diarios.
¿Cuánto te cuesta hoy seguir perdiendo oportunidades por no tener estructura?
¿Prefieres ahorrar ese dinero o usarlo para construir el sistema que te devolverá tu tiempo?"""
    },
    "obj_time": {
        "strategy": "Paradox",
        "script": """Sé que sientes que el día no te alcanza.
Justamente por eso necesitas esto. El programa no es para darte más tareas, es para quitarte las que no sirven y ordenarte.
Si seguimos igual, ¿cómo te ves en 6 meses? ¿Más libre o más saturada?"""
    },
    "obj_partner": {
        "strategy": "Business Plan",
        "script": """Qué bueno que tomes decisiones en equipo.
Mi consejo: No le pidas permiso, preséntale un plan de negocios.
Invítalo a ver los números y el retorno de inversión. ¿Te ayudo con eso?"""
    },
    "medical_condition": {
        "strategy": "Empathy Protocol",
        "script": """¡Tu bienestar es primero!
El programa es seguro, pero en casos de ansiedad clínica o embarazo, siempre consulta a tu médico.
Camila ofrece adaptaciones suaves para las respiraciones. Eres bienvenida y cuidada aquí."""
    },
    "is_ai": {
        "strategy": "Transparency",
        "script": """Soy la Asistente IA de Visionarias, entrenada con la metodología de Camila para darte claridad inmediata.
Sin embargo, la entrevista de admisión de 15 min es 100% humana y en vivo. Yo solo preparo el camino. ¿Seguimos?"""
    },
    "tech_issue": {
        "strategy": "Manual Rescue",
        "script": """¡La tecnología a veces falla!
Por favor déjame tu WhatsApp y correo aquí mismo. Le pasaré tus datos a la asistente personal de Camila para que te contacte manualmente en unos minutos."""
    }
}

def get_script(intent_key: str) -> str:
    """Retrieves the script content for a given intent."""
    item = SCRIPTS_REGISTRY.get(intent_key)
    if item:
        if "script" in item:
            return item["script"]
        return item["text"]
    return None
