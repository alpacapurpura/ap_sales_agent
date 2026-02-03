from enum import Enum

class OfferType(str, Enum):
    """
    Defines the logistical nature of the offer.
    """
    # --- NIVEL 1: ENTRADA Y BAJO COSTO ---
    N1_DIY_FREE_RESOURCE_MAGNET = "FREE_RESOURCE_MAGNET" # Lead magnets, Webinars gratuitos.
    N1_DIY_DIGITAL_PRODUCT = "DIGITAL_PRODUCT"           # Ebook, Curso grabado. Entrega inmediata.
    N1_DIY_MEMBERSHIP_SUBSCRIPTION = "MEMBERSHIP_SUBSCRIPTION" # Acceso a comunidad/contenido por pago recurrente bajo.

    # --- NIVEL 2: PUENTES Y DIAGNÓSTICO ---
    N2_DWY_PAID_AUDIT_DIAGNOSIS = "PAID_AUDIT_DIAGNOSIS" # Roadmapping, Auditoría técnica pagada.
    
    # --- NIVEL 3: TRANSFORMACIÓN (HIGH TICKET) ---
    N3_DWY_COHORT_PROGRAM = "COHORT_PROGRAM"             # Curso con fechas específicas de inicio y fin (Lanzamientos).
    N3_DWY_HYBRID_MENTORSHIP = "HYBRID_MENTORSHIP"       # Evergreen + Soporte (El estándar). # Contenido grabado + Soporte en vivo (El estándar High Ticket).
    N3_DWY_CONSULTING_PACKAGE = "CONSULTING_PACKAGE"     # Paquetes de horas/sesiones (Finito).

    # --- NIVEL 4: DELEGACIÓN Y SOCIEDAD (AGENCIA/DFY) ---
    N4_DFY_SERVICE_RETAINER = "SERVICE_RETAINER"         # Pago mensual por servicio recurrente (Agencia).
    N4_DFY_PERFORMANCE_REV_SHARE = "PERFORMANCE_REV_SHARE" # Cobro por resultados (% o CPA).

    # --- NIVEL 5: EXPERIENCIA Y ESTATUS (ULTRA HIGH) ---
    N5_DWY_MASTERMIND_NETWORK = "MASTERMIND_NETWORK"     # Acceso a pares, networking, sin temario.
    N5_DWY_LIVE_EVENT_RETREAT = "LIVE_EVENT_RETREAT"     # Evento físico o retiro exclusivo.

class OfferValueLevel(str, Enum):
    """
    Define el valor percibido por el cliente, y tiene relación con el costo de la oferta. Nos permite ofrecer de acuerdo al nivel de confianza inicial y/o capacidad adquisitiva.
    """
    N1 = "N1" # Entrada y bajo costo.
    N2 = "N2" # Puentes y diagnóstico.
    N3 = "N3" # Transformación (High Ticket).
    N4 = "N4" # Delegación y sociedad (Agencia/DFY).
    N5 = "N5" # Experiencia y estatus (Ultra High).

#Cambias a OfferValueLadder
class DeliveryModel(str, Enum):
    """
    Defines the level of service and justifies the price.
    """
    DIY = "DIY" # Do It Yourself: "Te doy el mapa, tú caminas". (Bajo precio, alto margen).
    DWY = "DWY" # Do It With You: "Caminamos juntos, te corrijo si te caes". (Ticket medio/alto).
    DFY = "DFY" # Do It For You: "Yo camino por ti, te cargo". (Ticket muy alto).

class GuaranteeType(str, Enum):
    """
    Risk Reversal strategy.
    """
    UNCONDITIONAL_30_DAY = "UNCONDITIONAL_30_DAY" # "Devolución sin preguntas"
    CONDITIONAL_ACTION_BASED = "CONDITIONAL_ACTION_BASED" # "Si haces la tarea y no funciona, te devuelvo"
    PERFORMANCE_REV_SHARE = "PERFORMANCE_REV_SHARE" # "No pagas hasta que ganes X"
    NO_REFUNDS = "NO_REFUNDS" # Venta final

class OfferStatus(str, Enum):
    """
    Availability status for scarcity/urgency.
    """
    ALWAYS_ON = "ALWAYS_ON" # Se puede comprar 24/7.
    WAITLIST_ONLY = "WAITLIST_ONLY" # Solo capturar lead.
    APPLICATION_CLOSED = "APPLICATION_CLOSED" # Cupos llenos.

class DeliverableFormat(str, Enum):
    """
    Format of the deliverable item.
    """
    LIVE_CALL = "LIVE_CALL"
    RECORDED_CONTENT = "RECORDED_CONTENT"
    PDF = "PDF"
    ONE_ON_ONE_CALL = "1ON1_CALL"

# --- NEW ENUMS FOR SPECIFIC DETAILS ---

class ProductFormat(str, Enum):
    DIGITAL_DOWNLOAD = "DIGITAL_DOWNLOAD"
    PHYSICAL_GOODS = "PHYSICAL_GOODS"
    HYBRID = "HYBRID"

class ServiceCapacity(str, Enum):
    OPEN = "OPEN"
    WAITLIST = "WAITLIST"
    CLOSED = "CLOSED"

class ProgramType(str, Enum):
    EVERGREEN = "EVERGREEN"
    COHORT_BASED = "COHORT_BASED"
    ONE_ON_ONE = "ONE_ON_ONE"

class BillingFrequency(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"

# --- HIGH TICKET DIMENSIONS ---

class PaymentPlanType(str, Enum):
    """
    Define la estrategia financiera y logística de cobro.
    Permite al Agente negociar basándose en la liquidez del cliente.
    """
    PAY_IN_FULL = "PAY_IN_FULL"          # Pago único (Suele tener descuento o bonus extra).
    SPLIT_PAY = "SPLIT_PAY"              # Financiación interna (Ej: 3 cuotas de $1000).
    THIRD_PARTY_FINANCE = "3RD_PARTY"    # Financiación externa (Ej: Klarna, PayPal Credit).
    SUBSCRIPTION_FOREVER = "SUBSCRIPTION" # Pago recurrente indefinido.

class AccessDuration(str, Enum):
    """
    Define la temporalidad del acceso al producto vs. el servicio.
    Crucial para manejar expectativas y evitar 'clientes eternos' sin pagar mantenimiento.
    """
    LIFETIME_ACCESS = "LIFETIME"        # Acceso de por vida (común en cursos N1/N2).
    LIMITED_TIME = "LIMITED_TIME"       # Acceso x meses (común en Cohortes).
    DURATION_OF_PAYMENT = "DURATION_OF_PAYMENT" # Solo mientras pagues (Membresías).
    HYBRID_ACCESS = "HYBRID_ACCESS"     # Contenido de por vida, Soporte por 6 meses.

class PrerequisiteType(str, Enum):
    """
    Criterios de 'Hard Gating' (Filtrado Duro).
    Permite al Agente descalificar leads que no cumplen requisitos técnicos o financieros mínimos.
    """
    REVENUE_LEVEL = "REVENUE_LEVEL"       # Ej: "Solo para facturación > $10k/mes".
    TECHNICAL_SKILL = "TECHNICAL_SKILL"   # Ej: "Debes saber Python básico".
    INDUSTRY_NICHE = "INDUSTRY_NICHE"     # Ej: "Solo para dueños de agencia, no eCommerce".
    GEOGRAPHIC = "GEOGRAPHIC"             # Ej: "Solo residentes en España".

class OnboardingMechanism(str, Enum):
    """
    Define la acción inmediata post-compra (La 'Next Best Action').
    Instruye al Agente sobre cómo cerrar la interacción (Link vs. Agenda).
    """
    INSTANT_REDIRECT_URL = "REDIRECT"           # Redirige a página de gracias/descarga.
    CALENDAR_BOOKING = "CALENDAR"               # Agenda la llamada de Kick-off.
    MANUAL_APPROVAL_WAIT = "MANUAL_WAIT"        # "Tu pago entró, un humano te escribirá en 24h".
    COMMUNITY_INVITE_LINK = "COMMUNITY_LINK"    # Link a Discord/Slack.

