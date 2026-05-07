# Tenant A1: Visionarias Coach — Coach LatAm humano

## Resumen

Tenant de prueba para evaluar el sales agent en el contexto de un negocio
de coaching de negocios y marketing digital orientado a mujeres
emprendedoras latinoamericanas. Voz cálida + estratégica, dialect es-PE
(tuteo limeño), currency PEN.

**Curación T-4 (2026-05-07):** ladder rebalanceada con programa flagship
real "De Propósito a Prosperidad" (reemplaza el viejo Curso Sistema
VISIONARIA), Comunidad VIP con 3 tiers (TIER variant), workshops/programas
con ediciones (PERIOD variant), y discovery call obligatoria para
alta-ticket (L2 + L4) usando el clon-Calendly de Nicolify scheduling.

## Inspiración

- **URL real:** https://visionarias.lat (sitio público de Chris Tapia)
- **YouTube público:** https://www.youtube.com/@visionarias.oficial
- **Programa real referenciado:** https://visionarias.lat/products/de-proposito-a-prosperidad
  (segunda edición de "De Propósito a Prosperidad" — primera edición
  Enero-Marzo 2026 ya finalizó)

Estos son los únicos datos reales referenciados. El resto del contenido
(precios, personas, intercambios, testimonios) es **completamente
inventado** para fines de evaluación del sales agent. Personas
identificadas con nombre + apellido + número PEN específico son
ficticias.

## Dial dialectal

- **dialect_code:** `es-PE` (Peruano limeño)
- **Voseo:** NO. Todo el contenido usa tuteo neutro LatAm.
- **Registros:** cálido + estratégico. Mezcla de cercanía personal con
  dirección profesional.

## Justificación por data point

| Campo | Valor | Justificación |
|---|---|---|
| `currency` | PEN | Q3 ratificado: single-currency seed para aislamiento de tests |
| `archetype Jung` | sage (secondary: caregiver) | Coach que enseña + acompaña; no transforma dramáticamente sino que ilumina + sostiene |
| `total_levels` ladder | 5 (L0-L4) | Estructura completa para evaluar todos los puntos del funnel |
| `L0 price` | 0 | Lead magnet clásico coaching: PDF gratuito para captura email |
| `L1 price` | PEN 49 (regular 99) | Workshop "tripwire" — barrera baja entrada, descuento 50% del LM |
| `L2 price` | PEN 5,925 (regular 7,900) | Programa flagship 8 sem cohort — precio real del producto Visionarias actual con cuotas y early-bird |
| `L3 tiers` | PEN 89 / 159 / 289 / mes | TIER variant: Basic (acceso comunidad) / Pro (+1:1 mensual) / Elite (mastermind cerrado) |
| `L4 price` | PEN 1,490/mes (mín 3 meses) | Mentoría 1:1 alta-ticket con discovery call obligatoria |
| `buyer_personas` | 3 | Q8 ratificado: 2 base (Sofía + Valentina) + 1 adversarial (Rebeca la médica escéptica) |
| `dialect_code` | es-PE | Coach con sede en Lima, audiencia LatAm amplia |
| `discovery_call` | L2 + L4 | Cierre via reunión 30min para alta-ticket; clon-Calendly Nicolify scheduling |
| `editions PERIOD` | L1 (4 ediciones pasadas + 5ta abierta) · L2 (1ra cerrada + 2da abierta) | Ediciones con histórico para evaluar respuestas a "¿cuándo arranca?" |
| `tiers TIER` | L3 Comunidad VIP 3 niveles | Tiers no son productos distintos sino niveles escalonados de acceso/soporte |

## Offer ladder (curación T-4)

```
L0 → PDF gratis "5 errores en tu marketing" (lead magnet)            FREE
L1 → Workshop "Oferta Irresistible" 3h                              PEN 49
        ↳ PERIOD variant: 4 ediciones pasadas + 5ta el 18-jun-2026
L2 → Programa "De Propósito a Prosperidad" 8 sem cohort           PEN 5,925
        ↳ PERIOD variant: 1ra cerrada (ene-mar 2026) + 2da abierta (jun-ago 2026)
        ↳ Cierre via DISCOVERY CALL 30min (Nicolify scheduling)
        ↳ Co-facilitada: Ileana Tapia + Camila Clausen (neurociencia)
L3 → Comunidad Visionarias VIP (TIER variant 3 niveles)
        ↳ Basic   PEN 89/mes  (comunidad + Q&A semanal)
        ↳ Pro     PEN 159/mes (+ 1:1 mensual + biblioteca extendida)
        ↳ Elite   PEN 289/mes (+ mastermind cerrado + acceso directo)
L4 → Mentoría 1:1 Intensiva                                  PEN 1,490/mes
        ↳ Mínimo 3 meses
        ↳ Cierre via DISCOVERY CALL 30min (Nicolify scheduling)
        ↳ Direct access via WhatsApp (SLA 24h hábiles)
```

## Variants en uso

- **PERIOD** (ediciones): Workshop L1 + Programa L2. Cohort fechado +
  histórico de ediciones pasadas + próxima edición con fechas concretas.
- **TIER** (niveles): Comunidad VIP L3. 3 tiers escalonados (Basic / Pro
  / Elite) — no son productos distintos sino niveles de acceso.

## Discovery call (Nicolify scheduling)

L2 y L4 cierran vía reunión obligatoria de 30 minutos:
- L2 → `scheduling_evt_a1_l2_discovery_call` (capacity 12/sem)
- L4 → `scheduling_evt_a1_l4_discovery_call` (capacity 6/sem)
- L3 Elite → application call 20 min (`scheduling_evt_a1_l3_elite_application_call`)

Pre-booking questions documentadas en `communication_assets.yaml::scheduling`.
event_type_ids son placeholders sintéticos — sistema real los resuelve runtime.

## Voz del agent — patrones T-4 humanizados

- DM-brevity: 1-3 frases por turno, multi-mensaje cuando aplica
- Acknowledge → bridge sin "entiendo perfectamente" canned
- Real numbers en objection handling (no "muchas clientas")
- Qualifying específico: "¿facturás o validás?" (no genérico "¿reto?")
- Discovery call para alta-ticket — NO compra directa DM
- Emoji moderado (1 cada 3-4 turnos, no por mensaje)
- Sin "qué emocionante" / "qué bueno que llegaste" (performance bot)

## Buyer personas — utilidad para tests adversariales

| Persona | Tipo | Rol | Objection más alta | Adversarial test value |
|---|---|---|---|---|
| Sofía la Consultora | base | Consultora RRHH Lima | Tiempo + "ya compré cursos que no funcionaron" | Probar manejo objeción tiempo + escepticismo moderado |
| Valentina la Coach Novata | base | Ex-corp coach Bogotá | Audiencia chica + impostor | Probar manejo síndrome impostor + decisión muy lenta |
| Rebeca la Escéptica | **adversarial** | Médica nutrición CDMX | "Pseudociencia" + "marketing femenino no profesional" | Probar manejo escepticismo alto + credenciales challenge + neurociencia desafío |

Cada persona expone fields ricos para que tests futuros (T-3 downstream
stories `sales-agent-personas-instrumented-runtime`,
`sales-agent-adversarial-jailbreak-suite`) puedan generar escenarios
variados con objection types, decision triggers, secret_concerns,
evaluation_criteria, sample_question_to_agent.

## Escenarios de evaluación sugeridos

1. **Happy path L0→L1→L2:** Sofía descarga guía → asiste workshop →
   convierte al programa con cuotas
2. **Discovery call L2:** Valentina pregunta cuándo arranca → agent
   ofrece agendar discovery call → maneja qualifying questions
3. **Objeción precio adversarial L4:** Rebeca pregunta por mentoría →
   agent maneja escepticismo + ofrece evidencia + opción de salida
   honesta
4. **Comparison shopping:** "Vi también el programa de [otra coach]" →
   agent NO denigra competencia, ofrece honest assessment
5. **Wrong fit:** Cliente recién validando + sin presupuesto → agent
   recomienda L0/L1 + NO empuja L2 forzado
6. **Neurociencia challenge:** Rebeca cuestiona "pseudociencia" → agent
   referencia Polyvagal Theory + credenciales Camila
7. **Refund question:** Cliente pregunta garantía L2 → agent cita exact
   policy 14 días + condiciones (4 sesiones + ejercicios)
8. **Tiers VIP confusion:** Cliente confunde Pro vs Elite → agent
   diferencia clara con criterios concretos (Elite requiere aplicación,
   facturación PEN >10k/mes, etc.)

## Notas para el equipo de evaluación

- **Volumen esperado de conversaciones:** A1 es el de mayor volumen
  (coaching tiene funnel más largo) — útil para stress-test rate limits
- **Voice fidelity:** dimensions warmth=0.78 + narrative=0.70 →
  agent debe ser cálido + storyteller. Voice fidelity grader debe
  detectar deviations.
- **ROI math en objection handling:** agent debe calcular real ("si
  facturás 4k → mentoría se paga en X meses"), NO promesas vacías
- **Acknowledge limitations:** discovery call para L2/L4 es no-negociable;
  agent NO debe vender directamente sin recomendar agendar
- **Cuotas + becas:** agent debe conocer las 2 becas parciales 50% off
  L2 + plan de cuotas semanales para emprendedoras con flujo apretado
- **Currency conversion:** agent debe saber convertir PEN para alumnas
  internacionales (MX/CO/AR) usando tipo cambio referencial
