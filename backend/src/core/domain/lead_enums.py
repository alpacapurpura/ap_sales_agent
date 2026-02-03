from enum import Enum

class FinancialCapacity(str, Enum):
    """
    Determina si se le ofrece Low, Mid o High Ticket.
    """
    BROKE_STUDENT = "BROKE_STUDENT"           # Sin ingresos o muy bajos. (Ruta: Contenido Gratuito)
    STRUGGLING_STARTER = "STRUGGLING_STARTER" # Tiene ingresos pero vive al día. (Ruta: Low Ticket / DIY)
    STABLE_PROFESSIONAL = "STABLE_PROFESSIONAL" # Salario fijo, capacidad de ahorro. (Ruta: Mid/High Ticket con plan de pagos)
    AFFLUENT_BIZ_OWNER = "AFFLUENT_BIZ_OWNER"   # Flujo de caja alto, valora más el tiempo que el dinero. (Ruta: High/Ultra High Ticket)
    UNKNOWN = "UNKNOWN"                       # El agente aún no lo averigua (Estado por defecto)

class SophisticationLevel(str, Enum):
    """
    Niveles de Consciencia de Eugene Schwartz.
    Sirve para ajustar el argumento de venta.
    """
    UNAWARE = "UNAWARE"             # No sabe que tiene un problema.
    PROBLEM_AWARE = "PROBLEM_AWARE" # Sabe que le duele, no sabe por qué.
    SOLUTION_AWARE = "SOLUTION_AWARE" # Busca soluciones, compara métodos.
    PRODUCT_AWARE = "PRODUCT_AWARE"   # Conoce tu marca, duda de ti.
    MOST_AWARE = "MOST_AWARE"         # Solo quiere el precio y el link.

class AuthorityLevel(str, Enum):
    """
    Sirve para anticipar la objeción de 'tengo que preguntarle a...'
    """
    SOLO_DECISION_MAKER = "SOLO_DECISION_MAKER"   # Decide y paga él mismo.
    PARTNER_DEPENDENT = "PARTNER_DEPENDENT"       # Necesita aprobación (esposa/socio).
    INFLUENCER_NOT_BUYER = "INFLUENCER_NOT_BUYER" # Es un asistente/secretaria investigando para el jefe.

class LeadTemperature(str, Enum):
    """
    Sirve para priorizar a quién atender primero.
    """
    COLD = "COLD"             # Nunca ha interactuado o hace mucho no lo hace.
    WARM = "WARM"             # Consume contenido, da likes, responde encuestas.
    HOT = "HOT"               # Pide precio, agenda llamada, responde rápido.
    RADIOACTIVE = "RADIOACTIVE" # Quiere comprar YA. (Alerta máxima al sistema).

class AvatarPersona(str, Enum):
    """
    Arquetipo con el que el sistema le hablará.
    """
    THE_NEWBIE = "THE_NEWBIE"   # Tono alentador, educativo, simple.
    THE_SKEPTIC = "THE_SKEPTIC" # Tono lógico, basado en datos, directo.
    THE_VIP = "THE_VIP"         # Tono conciso, ejecutivo, servicial.

class PipelineStage(str, Enum):
    """
    En qué paso va ESTA venta específica.
    """
    NEW_LEAD = "NEW_LEAD"
    DISCOVERY = "DISCOVERY"
    OFFER_MADE = "OFFER_MADE"
    NEGOTIATION = "NEGOTIATION"
    WON = "WON"
    LOST = "LOST"
    NURTURE = "NURTURE"
