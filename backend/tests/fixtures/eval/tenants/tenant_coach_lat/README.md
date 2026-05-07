# Tenant A1: Visionarias Coach — Coach LatAm humano

## Resumen

Tenant de prueba para evaluar el sales agent en el contexto de un negocio de
coaching de negocios y marketing digital orientado a mujeres emprendedoras
latinoamericanas.

## Inspiración

- **URL real:** https://visionarias.lat (sitio público de Visionarias)
- **YouTube público:** https://www.youtube.com/@visionarias.oficial
- Estos son los únicos datos reales referenciados. El resto del contenido
  (precios, personas, intercambios) es **completamente inventado** para
  fines de evaluación del sales agent.

## Dial dialectal

- **dialect_code:** `es-PE` (Peruano limeño)
- **Voseo:** NO. Todo el contenido usa tuteo neutro LatAm.
- **Registros:** cálido + estratégico. Mezcla de cercanía personal con
  dirección profesional.

## Justificación por data point

| Campo | Valor | Justificación |
|---|---|---|
| `currency` | PEN | Q3 ratificado: single-currency seed para aislamiento de tests |
| `L0 price` | 0 | Lead magnet clásico coaching: PDF gratuito para captura de email |
| `L1 price` | PEN 49 | Workshop accesible como "quick win", barrera baja de entrada |
| `L2 price` | PEN 297 | Curso de 8 semanas, precio típico LatAm para infoproductos mid-tier |
| `L3 price` | PEN 89/mes | Membresía de comunidad, precio accesible para retención |
| `L4 price` | PEN 1,490/mes | Mentoría 1:1 premium, precio refleja valor personalizado |
| `buyer_personas` | 3 | Q8 ratificado: 2 base (Sofía + Valentina) + 1 adversarial (Rebeca) |
| `dialect_code` | es-PE | Coach con sede en Lima, audiencia LatAm amplia |
| `archetype Jung` | sage | Coach que enseña y guía; no transforma dramáticamente sino que ilumina |

## Offer ladder

```
L0 → PDF gratis "5 errores en tu marketing" (lead magnet)
L1 → Workshop 3h "Oferta Irresistible"        PEN 49
L2 → Curso "Sistema VISIONARIA Completo"       PEN 297
L3 → Comunidad Visionarias VIP (mensual)       PEN 89/mes
L4 → Mentoría 1:1 Intensiva (mínimo 3 meses)  PEN 1,490/mes
```

## Escenarios de evaluación sugeridos

1. **Happy path:** Sofía la Consultora descarga guía → asiste workshop → compra curso
2. **Objeción precio:** "Es mucho dinero" → agent deflecta al valor transformacional
3. **Escéptica adversarial:** Rebeca la Médica con múltiples objeciones fuertes
4. **Upsell:** Alumna del curso que quiere más → mentoría 1:1

## Notas para el equipo de evaluación

- El tenant A1 es el de mayor volumen de conversaciones esperadas (coaching
  tiene el funnel más largo de los 5 tenants).
- La personalidad (dimensions) tiene warmth=0.78: el agent debe ser notablemente
  cálido y validador emocionalmente.
- Narrative=0.70: el agent cuenta historias de clientas frecuentemente.
- Para objeciones de precio, el agent debe mencionar el ROI y las cuotas
  disponibles, no bajar el precio directamente.
