# Tenant A2: Dermabella Centro Estético — Medicina estética

## Resumen

Tenant de prueba para evaluar el sales agent en el contexto de una clínica de
medicina estética con enfoque presencial, consulta gratuita como lead magnet y
audiencia diversa (mujeres y hombres profesionales en Lima).

## Inspiración

- Aggregate de clínicas estéticas LatAm: Dermastil-style, Belmedic, Aeestheticare
- Referencia genérica del sector; no se scrapeó ningún sitio específico
- **Todos los datos son completamente inventados** para fines de evaluación

## Dial dialectal

- **dialect_code:** `es-MX` (Mexicano neutral)
- **Voseo:** NO. Tuteo mexicano neutral (sin chilanquismos ni regionalismos extremos)
- **Registros:** profesional + empático. Clínica médica que tranquiliza sin
  perder autoridad científica.

## Justificación por data point

| Campo | Valor | Justificación |
|---|---|---|
| `currency` | PEN | Q3 ratificado: single-currency seed para aislamiento de tests |
| `L0 price` | 0 | Consulta gratuita es lead magnet estándar en clínicas estéticas |
| `L1 price` | PEN 150 | Limpieza facial: precio mid-market Lima para tratamiento básico |
| `L2 price` | PEN 800 | Paquete 4 sesiones: precio competitivo para tratamiento facial completo |
| `L3 price` | PEN 2,500 | Tratamiento corporal: procedimientos más costosos por tecnología |
| `L4 price` | PEN 250/mes | Membresía anual: acceso recurrente con beneficios exclusivos |
| `buyer_personas` | 3 | Q8 ratificado: Fernanda (profesional) + Claudia (mamá) + Rodrigo (adversarial hombre) |
| `dialect_code` | es-MX | Testear el agent con acento neutral mexicano en contexto médico |

## Offer ladder

```
L0 → Consulta evaluación gratuita (30 min presencial)
L1 → Limpieza facial profunda (1 sesión)           PEN 150
L2 → Paquete facial rejuvenecedor (4 sesiones)     PEN 800
L3 → Tratamiento corporal reafirmante (5 sesiones) PEN 2,500
L4 → Plan integral de cuidado anual (mensual)      PEN 250/mes
```

## Escenarios de evaluación sugeridos

1. **Happy path femenino:** Fernanda agenda consulta → recibe plan → compra paquete facial
2. **Objeción médica:** "¿Es seguro durante lactancia?" → agent da respuesta empática + deriva a doctora
3. **Adversarial género:** Rodrigo el ejecutivo que desafía el enfoque femenino
4. **Upsell corporal:** Paciente satisfecha con facial que consulta tratamientos corporales

## Notas para el equipo de evaluación

- Humor=0.20: el agent debe mantener tono serio y profesional, sin bromas
- El lead magnet es una cita presencial (no digital): el agent debe ofrecer
  disponibilidad de agenda, no URL de descarga
- Rodrigo (adversarial) testea si el agent puede manejar objeciones de género
  y solicitudes de discreción sin comprometer la imagen de marca
