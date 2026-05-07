# Tenant A4: Brote Agencia — Growth Marketing con video y RRSS

## Resumen

Tenant de prueba para evaluar el sales agent en el contexto de una agencia
boutique de growth marketing. Característica clave: SIN lead magnet (no tiene L0).
La agencia entra por portfolio/RRSS → audit (L1) como primer punto de pago.

## Inspiración

- Aggregate de agencias: brander.studio, toga.pe, agencias growth Argentina
- **Todos los datos son completamente inventados** para fines de evaluación
- No se scrapeó ningún sitio específico

## Dial dialectal

- **dialect_code:** `es-AR` (Rioplatense argentino — voseo legítimo)
- **Voseo:** SI. Los sample_exchanges usan voseo auténtico (vos/sos/tenés/podés/dale)
- **Magic comment:** `<!-- voseo-allowed -->` presente en la primera línea del
  `personality_profile.yaml` para evitar que el pre-commit hook bloquee el commit
- **Registros:** directo, irreverente, creativo. No endulza promesas.

## Edge case: SIN L0

Este tenant intencionalmente NO tiene nivel L0 (lead magnet). El loader emitirá:
```
structlog warning: offer_ladder_missing_lead_magnet
  tenant_slug=tenant_agencia_growth_video
```
El flag `has_lead_magnet=False` estará activo. Downstream consumers deben
manejar este caso (no mostrar flow de lead magnet en simulaciones).

## Justificación por data point

| Campo | Valor | Justificación |
|---|---|---|
| `currency` | PEN | Q3 ratificado: single-currency seed para aislamiento de tests |
| `L0` | AUSENTE | A4 per spec: agencia entra por portfolio, no por lead magnet gratuito |
| `L1 price` | PEN 500 | Audit de growth: punto de entrada de bajo riesgo para agencia B2B |
| `L2 price` | PEN 1,200/mes | Producción video: servicio especializado sin gestión completa |
| `L3 price` | PEN 2,500/mes | Retainer completo: precio mid-market Lima para agencia boutique |
| `L4 price` | PEN 5,000/mes | Consultoría estratégica: premium para marcas con equipo interno |
| `buyer_personas` | 3 | Q8: Daniela (e-commerce) + Pablo (restaurantero) + Valentín (adversarial analítico) |
| `dialect_code` | es-AR | Testear el agent en voseo rioplatense en contexto B2B agencia |
| `archetype Jung` | creator | Agencia creativa que produce; no solo asesora |

## Offer ladder

```
L0 → [AUSENTE] — entra por Instagram/portfolio (trigger warning loader)
L1 → Audit de Growth (diagnóstico digital)        PEN 500 (one-time)
L2 → Paquete producción video (4 reels/mes)       PEN 1,200/mes
L3 → Retainer mensual gestión completa RRSS        PEN 2,500/mes
L4 → Consultoría estratégica (intensivo trimestral) PEN 5,000/mes
```

## Escenarios de evaluación sugeridos

1. **Happy path:** Daniela ve portfolio → quiere audit → empieza retainer L3
2. **Resistencia a cambio:** Pablo ya tiene alguien en redes, no quiere cambiar
3. **Adversarial analítico:** Valentín exige métricas contractuales y ROAS reales
4. **Debate build vs buy:** Prospecto evalúa contratar interno vs agencia

## Notas para el equipo de evaluación

- Humor=0.62 + Energy=0.72: el agent usa humor dry frecuentemente y tiene
  mucha energía. Puede ser directo y algo irreverente.
- Sin L0: el agent no debe ofrecer un "gratuito" que no existe. Si alguien
  pide algo gratis, puede ofrecer el audit como punto de entrada de bajo riesgo.
- Valentín (adversarial) testea si el agent puede manejar marketing managers
  sofisticados que usan lenguaje técnico de métricas.
- Es-AR auténtico: el eval debe verificar que el agent usa voseo de forma
  natural y consistente en todo el dialogo.
