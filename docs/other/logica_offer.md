# Lógica de Negocio: Entidad "Offer" (Oferta)

Este documento explica la estructura, propósito y relaciones de la entidad central del sistema: la **Oferta (Offer)**. Está diseñado para que analistas y desarrolladores entiendan cómo modelamos digitalmente un producto o servicio High Ticket.

---

## 1. Concepto General
En nuestro sistema, una **Oferta** no es solo un "producto con precio". Es una promesa empaquetada que incluye:
1.  **Qué entregamos** (El producto/servicio).
2.  **Cómo lo entregamos** (La logística).
3.  **A quién se lo vendemos** (El avatar y los requisitos).
4.  **Cómo lo cobramos** (La arquitectura financiera).

El objetivo del sistema es que un Agente IA pueda leer esta estructura y tener toda la información necesaria para **negociar, vender y entregar** sin intervención humana constante.

---

## 2. Dimensiones de la Oferta

La entidad `Offer` se compone de varios bloques lógicos (Dimensiones). Aquí explicamos cada uno:

### A. Identificación y Naturaleza (`OfferType` y `OfferValueLevel`)
Define "qué es" la oferta en la escalera de valor.
*   **Nivel 1 (Entrada):** Productos baratos o gratuitos (Lead Magnets, Ebooks) para ganar confianza.
*   **Nivel 2 (Puente):** Auditorías o diagnósticos pagados para demostrar autoridad.
*   **Nivel 3 (Transformación - High Ticket):** El núcleo del negocio. Programas de acompañamiento (Mentorías, Cohortes).
*   **Nivel 4 (Delegación):** Servicios "Done For You" (Agencia).
*   **Nivel 5 (Estatus):** Masterminds y eventos exclusivos.

**¿Por qué es importante?**
Permite al Agente saber que no debe usar técnicas de venta agresiva con un Ebook de $7, pero sí debe calificar profundamente antes de ofrecer un Mastermind de $20k.

### B. Modelo de Entrega (`DeliveryModel`)
Define "quién hace el trabajo".
*   **DIY (Do It Yourself):** "Te doy el curso, tú estudias". Bajo costo, alto margen.
*   **DWY (Do It With You):** "Lo hacemos juntos". Mentoría, soporte, corrección. Es el estándar High Ticket.
*   **DFY (Do It For You):** "Yo lo hago por ti". Agencia. Precio más alto.

### C. Arquitectura Financiera (`PricingStructure` y `PaymentPlanType`)
En High Ticket, el precio no es fijo; depende de la **forma de pago**.
*   **Pay in Full (Contado):** Precio con descuento. Incentiva la liquidez inmediata.
*   **Split Pay (Financiado):** Precio total más alto, dividido en cuotas. Reduce la barrera de entrada para el cliente pero aumenta el riesgo de impago.
*   **Anchor Price (Precio Ancla):** El "valor percibido" (generalmente más alto) que hace que el precio real parezca una oportunidad.

**Lógica de Negocio:** El Agente IA intentará primero cerrar al contado. Si detecta objeción de precio, "bajará" a ofrecer financiación como herramienta de negociación.

### D. Acceso y Soporte (`AccessDuration`)
Distingue dos conceptos que suelen confundirse:
1.  **Acceso al Contenido:** ¿Por cuánto tiempo puedo ver los videos? (Ej: De por vida).
2.  **Acceso al Soporte:** ¿Por cuánto tiempo puedo hacer preguntas al experto? (Ej: 6 meses).

**Problema que resuelve:** Evita que clientes de hace 3 años exijan soporte gratuito hoy, protegiendo la rentabilidad del tiempo del experto.

### E. Gatekeeping (Cualificación y `PrerequisiteType`)
No vendemos a cualquiera. El sistema tiene "porteros" (Gatekeepers) que bloquean la venta si no se cumplen requisitos:
*   **Hard Gating:** Requisitos obligatorios (Ej: "Debes facturar > $10k/mes"). Si no se cumple, el Agente **descalifica** y no presenta la oferta.
*   **Anti-Avatar:** Palabras clave negativas (Ej: "busco dinero fácil"). Si el lead las menciona, es marcado como "no apto".

### F. Logística Post-Venta (`OnboardingMechanism`)
Define qué pasa *inmediatamente* después de que la tarjeta pasa.
*   **Redirect:** Para productos simples (descarga inmediata).
*   **Calendar:** Para servicios High Ticket, el pago suele desbloquear una llamada de bienvenida (Kick-off) para iniciar el servicio formalmente.

---

## 3. Relaciones con Otras Entidades

### Offer <-> Lead (Cliente Potencial)
*   **Relación:** Una Oferta "califica" a un Lead.
*   **Lógica:** El Agente compara los atributos del Lead (presupuesto, nicho) contra los `prerequisites` de la Oferta. Si coinciden, hay "Match".

### Offer <-> Downsell/Upsell
*   **Relación:** Una Oferta apunta a otras ofertas alternativas.
*   **Lógica:**
    *   Si el cliente dice "Muy caro" -> El sistema busca el `downsell_offer_id` (Oferta de menor valor) y la presenta.
    *   Si el cliente compra -> El sistema busca el `upsell_offer_id` (Oferta complementaria) para maximizar el valor del cliente (LTV).

### Offer <-> Tenant (Negocio)
*   **Relación:** Multi-tenencia.
*   **Lógica:** Cada Oferta pertenece a un `Tenant` (Cliente de nuestra plataforma SaaS). Las ofertas de "Agencia A" son invisibles para "Agencia B".

---

## 4. Ejemplo de Flujo de Decisión del Agente

1.  **Análisis:** El Agente recibe un Lead interesado en "Mentoría Premium" (Nivel 3).
2.  **Verificación (Gatekeeping):** ¿El Lead cumple con el requisito `REVENUE_LEVEL > 5000` definido en la Oferta?
    *   *No:* El Agente ofrece el curso "Iniciación" (Nivel 1 - Downsell).
    *   *Sí:* Continúa.
3.  **Presentación:** El Agente presenta la promesa (`headline_promise`) y el precio ancla.
4.  **Negociación:**
    *   Cliente: "Es costoso para mí ahora".
    *   Agente: Consulta `pricing_options` y ofrece el plan `SPLIT_PAY` (3 cuotas).
5.  **Cierre:**
    *   Cliente paga.
    *   Agente ejecuta `onboarding_action` -> Envía link de Calendario para Kick-off.

---

Este documento debe servir como referencia única de verdad para entender *cómo piensa* el sistema sobre nuestros productos.
