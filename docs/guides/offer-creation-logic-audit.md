# Auditoría de Arquitectura de Creación y Tipos de Ofertas
> **Alcance:** Offer Studio (Tipos de Oferta, Lógica de Creación y Formularios Reutilizables).
> **Fecha:** 24 de Marzo de 2026
> **Objetivo:** Describir la lógica de creación, mapear componentes y detectar brechas de calidad enfocadas en solopreneurs.

---

## 1. Mapeo de Tipos de Ofertas (Offer Types)
El sistema está construido sobre una arquitectura polimórfica dividida en 7 niveles de la *Value Ladder*.

| Nivel de Valor | Categoría | Tipos de Oferta (OfferType) | Detalles Específicos Usados |
|----------------|-----------|------------------------------|-----------------------------|
| **Nivel 0** | Adquisición (Gratis) | `FREE_RESOURCE`, `CONTENT_ASSET_PODCAST` | `ProductDetails` |
| | | `COMMUNITY_LITE` | `SubscriptionDetails` |
| | | `FREE_WEBINAR_CHALLENGE` | `ProgramDetails` |
| **Nivel 1** | Activación (Low Ticket) | `TRIPWIRE_OFFER`, `SELF_PACED_COURSE`, `PHYSICAL_MERCH` | `ProductDetails` |
| | | `PAID_NEWSLETTER_SUBSCRIPTION` | `SubscriptionDetails` |
| **Nivel 2** | Escalabilidad (Mid) | `HYBRID_MENTORSHIP`, `COHORT_BASED_COURSE`, `GROUP_COACHING_PROGRAM` | `ProgramDetails` |
| **Nivel 3** | Profit Maximizer | `VIP_DAY_STRATEGY`, `ONE_ON_ONE_PRIVATE_MENTORING`, `DEEP_DIVE_AUDIT` | `ServiceDetails` |
| **Nivel 4** | Delegación (DFY) | `PRODUCTIZED_SERVICE`, `ECOMMERCE_DEVELOPMENT`, `MONTHLY_RETAINER`, `PERFORMANCE_REV_SHARE`| `ServiceDetails` |
| **Nivel 5** | Legado (Exclusivo) | `MASTERMIND_NETWORK`, `LUXURY_RETREAT` | `EventDetails` |
| **Nivel 6** | Corporativo (B2B) | `CORPORATE_TRAINING`, `BRAND_SPONSORSHIP`, `KEYNOTE_SPEAKING` | `ServiceDetails` |

---

## 2. Formularios Reutilizables (Section Registry)
La interfaz del editor (`offer-editor.tsx`) está orquestada por el `OFFER_BUILDER_CONFIG`. Según el tipo de oferta, se renderiza una combinación específica de estos formularios modulares:

1. **StrategyForm**: Define a quién va dirigida (Avatar) y el modelo de negocio.
2. **IdentityForm**: Nombre público y SKU interno.
3. **PsychologyForm**: Dolores, deseos y manejo de objeciones.
4. **PromiseForm**: La promesa principal y el resultado esperado (Outcome).
5. **ProductDetailsForm / ServiceDetailsForm / ProgramDetailsForm / EventDetailsForm / SubscriptionDetailsForm**: Formulario dinámico que inyecta la logística específica (ej. currículum para programas, SLA para servicios).
6. **InstructorsForm**: Quién imparte la oferta.
7. **ValueStackForm**: Los entregables concretos que componen la oferta para aumentar la percepción de valor.
8. **ResourcesForm**: Enlaces, VSLs y material de apoyo.
9. **GalleryForm**: Imágenes de la oferta.
10. **PricingForm**: Opciones de pago (Suscripción, Pago Único, Cuotas).
11. **ClosingForm**: Garantías, URL de checkout y onboarding.

---

## 3. Lógica Actual de Creación de Ofertas (Paso a Paso)

Cuando el usuario quiere crear una oferta nueva, el flujo lógico actual es:

1. **Trigger UI**: El usuario hace clic en el botón "Añadir a Nivel X" (`AddOfferCard`) en el Dashboard (`OfferLadderLayout`).
2. **Modal de Selección**: Se abre un diálogo pidiendo 2 datos:
   - Tipo de Oferta (Ej: Mentoría Híbrida).
   - Nombre de la Oferta (Ej: "Acelerador de Ventas").
3. **Mutación Inicial**: Al confirmar, el frontend envía una petición al backend (`offerApi.createOffer`) para crear un cascarón vacío en la Base de Datos con estado `DRAFT` y el `type` seleccionado.
4. **Redirección**: El usuario es redirigido a la URL del editor (`/offer-studio/offer/[ID]`).
5. **Renderizado Dinámico**: El `OfferEditor` consulta el `OFFER_BUILDER_CONFIG` y renderiza solo los formularios pertinentes para ese tipo. 
6. **Autoguardado por Secciones**: Al abrir una sección en el panel lateral (`OfferEditSheetManager`) y editar, los datos se validan contra un esquema Zod masivo (`OfferSchema`) y se envían mediante PATCH al backend al cerrar el panel.

### ⚠️ Análisis de Problemas en el Flujo de Creación
- **Fricción de Página en Blanco**: El flujo crea un "cascarón vacío" y deja al solopreneur frente a ~10 secciones complejas que llenar manualmente. Para alguien que no es experto en marketing, llenar la "Psicología" y la "Promesa" desde cero genera parálisis.
- **Desconexión con la Marca (Brand Studio)**: Al crear la oferta, el sistema no inyecta automáticamente la información que ya sabe de la marca (Ej: si la marca atiende a "Doctores", la oferta no pre-selecciona a los doctores como Avatar objetivo).

---

## 4. Análisis de Calidad por Tipo de Formulario y Puntos de Mejora

### A. Formularios de Servicios (`ServiceDetailsForm`)
- **Estado Actual**: Captura Categoría, Frecuencia, Días de Entrega (SLA), Rondas de Cambios y una Lista de Entregables.
- **Punto de Mejora Crítico**: La lista de entregables (`deliverables_list`) es un simple array de strings (`Input` separado por comas). 
  - *Problema*: Esto es insuficiente para justificar precios de Nivel 3 o 4 ($2,000+).
  - *Solución*: Convertirlo en un *Field Array* estructurado donde el usuario detalle "Entregable -> Formato -> Beneficio". Y, como detectamos en la auditoría previa, **urge** un campo de "Fuera de Alcance" (Out of Scope).

### B. Formularios de Productos (`ProductDetailsForm`)
- **Estado Actual**: Maneja bien si es físico o digital, y calcula el tiempo de consumo.
- **Punto de Mejora**: Falta el "Mecanismo de Consumo Rápido".
  - *Problema*: Los productos de Nivel 1 (Tripwires) sufren de baja tasa de consumo. Si el cliente no lo consume, no sube al Nivel 2.
  - *Solución*: Añadir un campo `quick_win_action` (Ej: "La primera plantilla que deben abrir"). Esto permite que el agente SDR o de Onboarding fomente una victoria temprana.

### C. Formularios de Programas (`ProgramDetailsForm`)
- **Estado Actual**: Excelente estructura. Captura fechas, límites de cohorte, plataformas de comunidad y un constructor de currículum.
- **Punto de Mejora**: Desconexión Promesa-Módulo.
  - *Problema*: El currículum se construye como un índice universitario ("Módulo 1: Introducción").
  - *Solución*: En el esquema `ProgramModule`, obligar al usuario a atar cada módulo a un `micro_outcome` (Hito de transformación). Esto permite al Copilot vender el programa por sus resultados intermedios, no por sus horas de video.

### D. Formulario de Suscripciones (`SubscriptionDetailsForm`)
- **Estado Actual**: Básico. Captura ciclo de facturación, prueba gratuita y política de cancelación.
- **Punto de Mejora**: Carece de mecánicas de retención.
  - *Problema*: El mayor dolor en las ofertas recurrentes (Nivel 4 o Nivel 1 continuo) es el *Churn* (cancelaciones).
  - *Solución*: Añadir `retention_mechanisms: List[str]` (Ej: "Llamada mensual de auditoría", "Reporte de progreso").

### E. Formulario de Cierre y Garantías (`ClosingForm`)
- **Estado Actual**: Usa un enum de `GuaranteeType` (Incondicional, Condicional, etc.) muy bien tipado.
- **Punto de Mejora**: Falta la métrica de "Riesgo Invertido" explícita.
  - *Problema*: Para cerrar High-Ticket, el SDR necesita verbalizar cómo la garantía elimina el riesgo.
  - *Solución*: Además del tipo de garantía, añadir un campo `risk_reversal_statement` generado por IA que convierta la garantía técnica en una frase de ventas conversacional.

---

## 5. Recomendación Arquitectónica (El Gran Cambio)

**Pasar de "Creación Manual" a "Generación Asistida por Copilot"**.

Actualmente, el botón "Crear Oferta" debería redirigir a un **"Offer Generation Wizard"** (Asistente de 3 pasos) antes de ir al editor completo:
1. **Paso 1**: ¿Qué vas a vender? (Selecciona el tipo).
2. **Paso 2**: ¿A quién de tus Avatares de Marca se lo vas a vender? (Hereda datos del Brand Studio).
3. **Paso 3**: Prompt de IA: Describe tu idea en 2 líneas.
4. **Magia**: El Copilot (backend) pre-llena los 15 formularios (`Promise`, `Psychology`, `Strategy`, `ValueStack`) basándose en las metodologías de Hormozi y Brunson.
5. **Resultado**: El usuario llega al `OfferEditor` no a escribir desde cero, sino a **editar y refinar** una oferta altamente persuasiva que ya tiene estructura de ventas.
