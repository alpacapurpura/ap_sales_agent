# Tenant A5: NovaByte Automatización IA — Agencia de Automatización con IA

## Resumen

Tenant de prueba para evaluar el sales agent en el contexto de una agencia
de automatización de procesos con IA para pymes LatAm. Característica clave:
SIN lead magnet (no tiene L0). La agencia entra por discovery call → auditoría (L1).

## Inspiración

- Aggregate de agencias tech LatAm: brandtech.pe + agencias IA Lima/Bogotá/Santiago
- **Todos los datos son completamente inventados** para fines de evaluación
- No se copió de OpenAI, Anthropic ni empresas de vibe-coding

## Dial dialectal

- **dialect_code:** `es-419` (Español neutro pan-LatAm)
- **Voseo:** NO. Tuteo neutro sin localismos ni regionalismos
- **Registros:** técnico pero accesible. Resuelve dudas con precisión sin jerga excesiva.

## Edge case: SIN L0

Este tenant intencionalmente NO tiene nivel L0 (lead magnet). El loader emitirá:
```
structlog warning: offer_ladder_missing_lead_magnet
  tenant_slug=tenant_agencia_automatizacion_ia
```
El flag `has_lead_magnet=False` estará activo.

**Nota importante sobre L1 "discovery call":**
El primer entry-point de la agencia es una discovery call (no cobrada), pero
este NO es un L0 lead magnet. La discovery call es una calificación de prospecto,
no un contenido descargable ni una consulta gratuita de servicio. El ladder
de precios empieza en L1 (auditoría PEN 1,000).

## Justificación por data point

| Campo | Valor | Justificación |
|---|---|---|
| `currency` | PEN | Q3 ratificado: single-currency seed para aislamiento de tests |
| `L0` | AUSENTE | A5 per spec: agencia IA entra por discovery call, no por contenido gratuito |
| `L1 price` | PEN 1,000 | Auditoría de procesos: diagnóstico técnico de 3 días |
| `L2 price` | PEN 8,000 | Implementación estándar: agente IA completo desplegado |
| `L3 price` | PEN 4,000/mes | Retainer operación: equipo técnico sin contratar |
| `L4 price` | PEN 8,000-12,000/mes | Programa transformación: múltiples automatizaciones |
| `buyer_personas` | 3 | Q8: Miguel (logística) + Sandra (e-commerce) + Lorenzo (adversarial CTO) |
| `dialect_code` | es-419 | Agencia con clientes pan-LatAm, lenguaje neutral técnico |
| `archetype Jung` | magician | Agencia que transforma procesos manuales en automáticos |

## Offer ladder

```
L0 → [AUSENTE] — entry por discovery call (trigger warning loader)
L1 → Auditoría de procesos IA (diagnóstico 3 días)       PEN 1,000
L2 → Implementación agente IA (paquete estándar)          PEN 8,000+
L3 → Retainer mensual operación IA                        PEN 4,000/mes
L4 → Programa automatización empresarial (6 meses)        PEN 8,000-12,000/mes
```

## Escenarios de evaluación sugeridos

1. **Happy path B2B:** Miguel (logística) llega por LinkedIn → auditoría → implementación
2. **Objeción experiencia previa:** Sandra "los chatbots que probé eran horrible"
3. **Adversarial técnico:** Lorenzo CTO que desafía seguridad, arquitectura y vendor lock-in
4. **Discovery call:** Prospecto que quiere la "llamada gratuita" → agent califica y propone auditoría

## Notas para el equipo de evaluación

- Humor=0.28: el agent es muy serio y técnico. Poco espacio para humor.
- El agent debe poder responder preguntas técnicas (API, SAP, seguridad) sin
  inventar respuestas; si no sabe, debe decirlo y proponer la auditoría.
- Lorenzo (adversarial) es el escenario más exigente: CTO técnicamente
  sofisticado que desafía la profundidad real de la agencia.
- El agent no debe inventar afirmaciones sobre regulaciones (SBS, datos) a
  menos que estén documentadas en el brand.yaml.
- Sin L0: si alguien pide algo gratis, el agent puede ofrecer la discovery
  call de calificación (no cobrada) como primer paso, pero debe ser claro
  que el primer entregable pagado es la auditoría de L1.
