# Tenant A3: Sonrisa Plena — Clínica Dental Miraflores

## Resumen

Tenant de prueba para evaluar el sales agent en clínica dental
integral en Lima (Miraflores). Voz cercana sin informal, técnica clara,
anti-sobreventa, dialect es-CO bogotano (founder colombiano), currency
PEN. CON L0 (primera consulta gratis con radiografía panorámica).

**Curación T-4 (2026-05-07):** ladder con benchmarks reales Lima 2026
(limpieza PEN 80-200, ortodoncia metálica PEN 2,500-5,000, Invisalign
PEN 4,000-8,000, implantes PEN 2,500-6,000). TIER variants en L2
ortodoncia (3 opciones: metálicos / cerámicos / Invisalign), L3
estética (3 opciones: Express / Completo / Premium con CBCT) y L4 Plan
Familiar (Pareja / Familia 4 / Familia 6). Discovery call obligatoria
L3+L4. Diferencial: plan escrito post-consulta = costo final exacto.

## Inspiración

Aggregate clínicas reales LatAm:
- **Solución Dental** (soluciondental.pe) — referente Lince precios
- **The Dental Clinic** (thedentalclinic.pe) — premium Miraflores+SI
- **Dental Krebs** (dentalkrebs.com) — boutique San Isidro
- **Smile Design Perú** (smiledesignperu.com) — especialistas estética
- **dentalindo.com** — referencia inicial story

Datos sintéticos. Founder ficticio Dr. Andrés Restrepo (colombiano
formación UNAL Bogotá + maestría UPCH Lima 2018-2020). Dirección Av.
Larco 1200 Miraflores plausible. CMP numbers + RUC placeholders. Otras
doctoras (Pinto, Vargas, Quispe) sintéticas.

## Dial dialectal

- **dialect_code:** `es-CO` (Bogotano tuteo, sin voseo paisa)
- **Voseo:** NO. Tuteo bogotano sin regionalismos extremos.
- **Registros:** cercano + claro técnicamente + anti-sobreventa.

## Justificación por data point

| Campo | Valor | Justificación |
|---|---|---|
| `currency` | PEN | Q3 ratificado single-currency seed |
| `archetype Jung` | caregiver (secondary: everyman) | Clínica familiar accesible que cuida sin elitismo |
| `total_levels` ladder | 5 (L0-L4) | Consulta gratis → limpieza → ortodoncia tiers → estética tiers → plan familiar tiers |
| `L0` | consulta gratis 45 min + panorámica + plan escrito | Lead magnet alta-intent — diferencial vs competencia |
| `L1` | PEN 80 (simple) / PEN 150 (completa) | Limpieza dental — rangos Lima 80-200 |
| `L2 tiers` | PEN 3,200 / 4,500 / 7,500 (Metálicos/Cerámicos/Invisalign) | TIER variant según preferencia estética + complejidad |
| `L3 tiers` | PEN 600 / 7,200 / 12,500 (Express/Completo/Premium) | TIER variant estética dental con DSD digital |
| `L4 tiers` | PEN 180/280/450 mensual (Pareja/Fam4/Fam6) | TIER variant Plan Familiar — predictibilidad gasto |
| `buyer_personas` | 3 | Q8 ratificado: 2 base (Carlos profesional + Verónica madre) + 1 adversarial (Renata influencer 380k) |
| `dialect_code` | es-CO | Founder Andrés colombiano formación Bogotá |
| `discovery call L3+L4` | obligatoria | Tratamientos premium requieren diagnóstico específico |
| `consulta L0 + panorámica gratis` | diferencial | Costo equivalente PEN 80 si compras suelta |
| `plan escrito = costo final` | diferencial documentado | vs cotizaciones vagas competencia |

## Offer ladder (curación T-4)

```
L0 → Primera consulta gratis 45 min + radiografía panorámica + plan escrito  GRATIS
        ↳ Presencial Av. Larco 1200 Miraflores
        ↳ Odontólogo titular según especialidad
        ↳ Plan con costo final cerrado (no 'depende del caso')
L1 → Limpieza dental (simple PEN 80 / completa PEN 150)
L2 → Ortodoncia (TIER variant 3 niveles)
        ↳ Brackets metálicos 3M Unitek      PEN 3,200 (24 meses promedio)
        ↳ Brackets estéticos cerámicos      PEN 4,500
        ↳ Alineadores Invisalign            PEN 7,500 (más popular adultos)
L3 → Estética dental (TIER variant 3 niveles)
        ↳ Express — Blanqueamiento Philips Zoom    PEN 600
        ↳ Completo — 4-8 carillas e-max + DSD      PEN 7,200 (más popular)
        ↳ Premium — Diseño completo + CBCT         PEN 12,500
        ↳ Cierre via DIAGNÓSTICO ESTÉTICO + DSD gratis
L4 → Plan Familiar mensual recurrente (TIER variant 3 niveles)
        ↳ Pareja      PEN 180/mes (2 personas)
        ↳ Familia 4   PEN 280/mes (más popular)
        ↳ Familia 6   PEN 450/mes
        ↳ Cierre via EVALUACIÓN FAMILIAR 30-45 min
```

## Variants en uso

- **TIER** (niveles): L2 ortodoncia (3 opciones técnicas) · L3 estética (3 niveles complejidad) · L4 plan familiar (3 tamaños familia)
- NO usamos PERIOD ni PACK en este tenant (cada servicio es transaccional individual o membresía)

## Discovery / cierre (Nicolify scheduling)

- **L0 = lead magnet + discovery** (consulta gratis + panorámica + plan escrito)
- **L3 → diagnóstico estético** con DSD digital (preview resultado antes de procedimiento)
- **L4 → evaluación familiar** 30-45 min con todos los miembros

## Voz del agent — patrones T-4 humanizados

- DM-brevity 1-3 frases multi-msg
- Acknowledge → bridge sin "entiendo perfectamente"
- Real numbers PEN específicos en cotizaciones (no "depende")
- Qualifying específico: "¿hace cuánto no vas?" "¿qué te interesa?"
- Comparativa honesta con competencia sin denigrar
- Bogotano tuteo — sin voseo paisa, sin regionalismos
- Anti-sobreventa explícito ("rara vez se necesitan carillas en todos los dientes")
- Plan escrito = costo final como mensaje recurrente

## Buyer personas — utilidad para tests adversariales

| Persona | Tipo | Rol | Objection más alta | Adversarial test value |
|---|---|---|---|---|
| Carlos el Profesional Joven | base | Ingeniero software 35 años | "¿La cotización incluye TODO o cobran controles aparte?" + "Otra clínica más barato" | Probar transparencia total + cuotas + comparativa honesta |
| Verónica la Madre de Familia | base | Profesora 42 años con esposo dental-fóbico + 2 hijos | "PEN 280×12 vs gasto suelto" + "esposo no va, ¿pierdo plata?" | Probar plan familiar logic + flexibilidad miembros + odontopediatría |
| Renata la Influencer | **adversarial** | Influencer beauty 28 años 380k IG | "Necesito 12 carillas mínimo" + "¿collab?" + "su clínica no es boutique-level" | Probar resistencia a sobreventa + manejo narcisismo profesional + decline collab |

## Escenarios de evaluación sugeridos

1. **Happy path L0 → L2 Invisalign:** Carlos profesional → primera consulta gratis → ClinCheck preview → 18 cuotas BCP
2. **Plan Familiar logic:** Verónica calcula PEN 280×12 vs gasto suelto histórico → agent muestra comparativa honesta
3. **Anti-sobreventa adversarial:** Renata pide 12 carillas → agent recomienda 6 con DSD + se mantiene firme
4. **Decline collab:** Renata ofrece collab → agent declina profesionalmente con razón (anti-sobreventa policy)
5. **Comparativa competencia honesta:** Carlos cita "otra clínica PEN 5,800 Invisalign" → agent pregunta qué incluye sin denigrar
6. **Esposo dental-fóbico:** Verónica pregunta si pierde dinero por miembro que no va → agent explica flexibilidad
7. **Pediatría:** Hijos 8+11 años → agent explica odontopediatría incluida + sellantes preventivos
8. **Insurance reembolso:** Cliente con Pacífico/Mapfre → agent explica proceso (paciente paga upfront, factura para reembolso)
9. **Implante complejo:** 3 piezas → agent ofrece opción puente sobre 2 implantes vs 3 individuales
10. **Miedo al dentista:** Esposo años sin ir → agent ofrece sedación consciente + ritmo paciente

## Notas para el equipo de evaluación

- **Plan escrito = costo final** es non-negotiable — agent debe insistir en esto vs cotizaciones vagas
- **Anti-sobreventa** documentada — agent rechaza tratamientos no necesarios (10-12 carillas si bastan 6)
- **Cuotas detalladas** por banco — BCP/Interbank/BBVA/Scotia/Banbif 3-18 cuotas según monto
- **Plan directo Sonrisa Plena** alternativa para clientes sin tarjeta (30% inicial + 12 mensualidades)
- **Insurance reembolso** activo con Pacífico/Mapfre/Rímac/Interseguro
- **Convenios corporativos** activos con 8 empresas (BCP, Interbank, Belcorp, Falabella)
- **DSD digital** (diseño de sonrisa digital) es diferencial clave para estética
- **Garantía escrita** 24-36 meses según tratamiento
- **Especialidades** rotan: Andrés (estética/general), Sandra (ortodoncia Invisalign), Laura (endodoncia)
- **Pediatría** con doctora externa martes/jueves
- **Línea emergencia 24/7** solo para pacientes activos
