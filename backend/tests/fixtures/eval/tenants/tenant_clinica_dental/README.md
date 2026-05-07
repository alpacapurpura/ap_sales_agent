# Tenant A3: Sonrisa Perfecta Clínica Dental — Odontología integral

## Resumen

Tenant de prueba para evaluar el sales agent en el contexto de una clínica
dental familiar con primera consulta gratuita, variedad de tratamientos y
enfoque en transparencia de precios.

## Inspiración

- **URL real de referencia:** https://dentalindo.com (portal de información dental Perú)
- Aggregate de clínicas dentales Lima (Sonrisas, DentalPro, clínicas de barrio)
- **Todos los datos son completamente inventados** para fines de evaluación

## Dial dialectal

- **dialect_code:** `es-CO` (Colombiano — tuteo bogotano)
- **Voseo:** NO. Tuteo bogotano formal, sin voseo paisa ni regionalismos extremos
- **Registros:** cálido + profesional. Dentista de confianza que no asusta.

## Justificación por data point

| Campo | Valor | Justificación |
|---|---|---|
| `currency` | PEN | Q3 ratificado: single-currency seed para aislamiento de tests |
| `L0 price` | 0 | Primera consulta gratuita: lead magnet estándar en odontología |
| `L1 price` | PEN 80 | Profilaxis: precio mid-market Lima para limpieza básica |
| `L2 price` | PEN 2,000 | Ortodoncia: precio base, variable por complejidad |
| `L3 price` | PEN 3,500 | Estética dental: carillas + blanqueamiento, precio premium |
| `L4 price` | PEN 250/año | Plan familiar: prevención anual con descuentos incluidos |
| `buyer_personas` | 3 | Q8: Patricia (mamá) + Carlos (joven profesional) + Don Augusto (adversarial resistente) |
| `dialect_code` | es-CO | Testear tono colombiano formal en contexto médico dental |

## Offer ladder

```
L0 → Primera consulta dental gratuita (con diagnóstico digital)
L1 → Profilaxis dental (limpieza profesional)          PEN 80
L2 → Tratamiento ortodoncia (brackets)                 PEN 2,000+
L3 → Estética dental completa (carillas+blanqueamiento) PEN 3,500
L4 → Plan Familia control anual                        PEN 250/año/persona
```

## Escenarios de evaluación sugeridos

1. **Happy path familia:** Patricia agenda para ella y sus hijos → consulta gratis → brackets hijo mayor
2. **Joven con expectativas:** Carlos quiere brackets invisibles para boda en 6 meses → diagnóstico claro
3. **Resistente clásico:** Don Augusto que no quiere ir al dentista pero lo manda su esposa
4. **Objeción presupuesto:** "No puedo pagar todo de golpe" → agent explica cuotas sin intereses

## Notas para el equipo de evaluación

- Humor=0.30: el agent puede usar humor sutil para aliviar tensión, especialmente
  en conversaciones sobre miedo al dentista
- El lead magnet es cita presencial (no digital): el agent gestiona agenda
- Don Augusto (adversarial) testea resistencia masculina al cuidado médico
  y desconfianza hacia diagnósticos "inventados"
- El agent debe manejar objeciones de precio sin bajar precios, usando las
  cuotas como argumento principal
