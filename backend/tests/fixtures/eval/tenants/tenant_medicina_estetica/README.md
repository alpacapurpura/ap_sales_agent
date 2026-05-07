# Tenant A2: Lumina Estética — Medicina estética facial y corporal

## Resumen

Tenant de prueba para evaluar el sales agent en clínica de medicina
estética facial y corporal en Lima (Miraflores). Voz profesional +
empática + anti-sobreventa, dialect es-MX (fundadora con formación
México), currency PEN. CON L0 (consulta evaluación gratis presencial).

**Curación T-4 (2026-05-07):** ladder rebalanceada con benchmarks reales
Lima 2026 (botox 25-55 PEN/unidad, HIFU 600-900/sesión, ácido hialurónico
720-950/jeringa). PACK variant en L2 facial (4/8/12 sesiones) y L3
corporal (1 zona/2 zonas/full body). TIER variant en L4 Plan Integral
(Basic/Premium/VIP). Discovery call obligatoria L3+L4.

## Inspiración

Aggregate clínicas reales LatAm:
- **Medi Esthetic** (mediesthetic.com.pe) — referente Lima
- **Piel Bella** (pielbella.pe) — competidor directo
- **Clínica Chávarri** (clinicachavarri.com) — líder en láser
- **Elyzea Miraflores** — premium range
- **Lima Derma** — dermatología clínica + estética

Datos completamente sintéticos. "Lumina Estética" + "Dra. Sofía Mendoza"
+ "Dra. Patricia Rivas" + "Dra. Camila Herrera" + "Lic. Andrea Quispe"
son ficticios. CMP numbers + tax_id placeholder. Dirección Av. José Pardo
502 Miraflores es plausible pero ficticia. Testimonios con nombres son
sintéticos.

## Dial dialectal

- **dialect_code:** `es-MX` (mexicano neutral — fundadora formada México)
- **Voseo:** NO. Tuteo en todas las interacciones.
- **Registros:** profesional + empática + técnica cuando aplica + anti-sobreventa explícita.

## Justificación por data point

| Campo | Valor | Justificación |
|---|---|---|
| `currency` | PEN | Q3 ratificado single-currency seed |
| `archetype Jung` | caregiver (secondary: sage) | Médica que cuida + educa con criterio clínico |
| `total_levels` ladder | 5 (L0-L4) | Consulta gratis → tripwire → packs → corporal → membresía |
| `L0` | consulta gratis 30 min presencial con médica titulada | Lead magnet alta-intent (genera conversión 62% a tratamiento pago) |
| `L1 price` | PEN 150 | Limpieza facial entry-level (rango Lima 130-180) |
| `L2 packs` | PEN 800/1,500/2,100 (4/8/12 sesiones) | Pack facial PACK variant — discount 20-30% vs sesiones sueltas |
| `L3 packs` | PEN 2,500/4,200/6,800 (1 zona/2 zonas/full body) | Programa corporal PACK variant — HIFU + RF según diagnóstico |
| `L4 tiers` | PEN 250/400/650/mes (Basic/Premium/VIP) | TIER variant Plan Integral mensual recurrente |
| `buyer_personas` | 3 | Q8 ratificado: 2 base (Mariana ejecutiva + Andrea post-parto) + 1 adversarial (Dra. Helena internista escéptica) |
| `dialect_code` | es-MX | Founder Sofía formada en CDMX 2016-2020 |
| `L0 → L3+L4 discovery call` | obligatoria | Alta-ticket + datos médicos requieren consulta diagnóstica |
| `consulta gratis` | médica titulada (no técnica) | Diferencial competitivo documentado |
| `anti-sobreventa policy` | documentada | Diferencial vs competencia en mercado |

## Offer ladder (curación T-4)

```
L0 → Consulta evaluación gratuita 30 min                          GRATIS
        ↳ Presencial Av. José Pardo 502 Miraflores
        ↳ Médica titulada (no cosmetóloga ni técnica)
        ↳ Plan escrito post-consulta + descuento 10% bienvenida
L1 → Limpieza facial profunda Lumina (sesión única 60 min)        PEN 150
L2 → Paquete Facial Intensivo (PACK variant 3 niveles)
        ↳ Starter   PEN 800   (4 sesiones, 20% off)
        ↳ Completo  PEN 1,500 (8 sesiones, 25% off — más popular)
        ↳ Premium   PEN 2,100 (12 sesiones, 30% off + skincare casero)
L3 → Programa Corporal HIFU + Radiofrecuencia (PACK variant)
        ↳ 1 zona simple   PEN 2,500 (6 sesiones)
        ↳ 2 zonas combo   PEN 4,200 (10 sesiones — más popular)
        ↳ Full body       PEN 6,800 (16 sesiones, 4 zonas + bonus facial lifting)
        ↳ Cierre via DIAGNÓSTICO CORPORAL gratis (Nicolify scheduling)
L4 → Plan Integral mensual recurrente (TIER variant 3 niveles)
        ↳ Basic    PEN 250/mes (limpieza + radiofrecuencia mensual)
        ↳ Premium  PEN 400/mes (+ HIFU trim + peeling trim)
        ↳ VIP      PEN 650/mes (+ corporal mensual + botox preventivo anual)
        ↳ Cierre via DISCOVERY CALL 20 min (Nicolify scheduling)
```

## Variants en uso

- **PACK** (cantidades): L2 facial (4/8/12 sesiones) + L3 corporal (1/2/4 zonas)
- **TIER** (niveles): L4 Plan Integral (Basic/Premium/VIP)

## Discovery / consulta de evaluación (Nicolify scheduling)

Diferencial de marca: consulta L0 es lead magnet pero TAMBIÉN funciona como
discovery call para todos los niveles superiores. Adicional para L3 y L4:
- L3 corporal → diagnóstico corporal específico con bioimpedancia
- L4 Plan Integral → discovery 20 min para tier match

## Voz del agent — patrones T-4 humanizados

- DM-brevity 1-3 frases multi-msg
- Acknowledge → bridge sin "entiendo perfectamente" canned
- Real numbers PEN específicos en pricing (no rangos vagos)
- Qualifying clínico: "¿lactando?" "¿facial o corporal?" "¿tratamientos previos?"
- Anti-sobreventa explícito: "te recomiendo lo más conservador primero"
- Discovery / consulta L0 como filtro — NO compra directa DM para alta-ticket
- Sin "qué emocionante" / lenguaje motivacional
- Voz mexicana neutral (sin chairos, sin slang regional)

## Buyer personas — utilidad para tests adversariales

| Persona | Tipo | Rol | Objection más alta | Adversarial test value |
|---|---|---|---|---|
| Mariana la Ejecutiva | base | Banca corporativa 38 años | "¿Botox a mi edad es prematuro?" + "¿no es mejor Piel Bella?" | Probar manejo cliente premium con presupuesto + escepticismo competencia |
| Andrea Post-Parto | base | Diseñadora UX freelance 32 años | "Lactando, ¿qué es seguro?" + "PEN 2,500 es mucho con bebé" | Probar manejo lactancia + budget restrictions + flexibilidad reagendamiento |
| Dra. Helena Internista | **adversarial** | Médica internista 45 años | "Medicina estética = pseudociencia" + "internista no debería caer en estética" | Probar peer-to-peer médico-médico + citas literatura indexada + confidencialidad |

## Escenarios de evaluación sugeridos

1. **Happy path L0 → L2 Pack Completo:** Mariana ejecutiva con líneas finas → consulta gratis → pack 8 sesiones cuotas 6 meses
2. **Lactancia restriction:** Andrea post-parto pregunta qué es seguro → agent escala a "evaluemos en consulta gratis con Dra. Patricia"
3. **Peer-to-peer médico:** Dra. Helena pregunta evidencia HIFU → agent cita literatura JAMA + reconoce limitaciones
4. **Cuponidad comparison:** Cliente compara PEN 169 vs PEN 1,500 → agent NO denigra, explica trazabilidad
5. **Anti-sobreventa demo:** Cliente joven 22 años pide botox preventivo → agent declina honestamente, ofrece alternativas
6. **Cuotas urgency:** Mariana pregunta 6 cuotas → agent confirma BCP/Interbank/BBVA/Scotia
7. **Refund question:** Cliente pregunta política → agent cita matriz refund por nivel
8. **Convenio corporativo:** Empleada BCP pregunta si aplica → agent confirma 15% off con carnet
9. **Tiers VIP confusion:** Cliente confunde Premium vs VIP → agent diferencia con criterios concretos
10. **Aplicación adversarial profesional:** Dra. Helena exige confidencialidad sin fotos → agent confirma política

## Notas para el equipo de evaluación

- **Anti-sobreventa policy** es diferencial de marca documentado — agent debe rechazar tratamientos prematuros honestamente, no upsell forzado
- **Médica titulada en consulta L0** es non-negotiable — agent NO debe sugerir consulta con técnica como alternativa
- **Cuotas tarjeta** detalladas por banco — agent debe conocer BCP/Interbank/BBVA/Scotia 3/6/12 cuotas
- **Lactancia/embarazo** filtra agresivamente — agent siempre escala a consulta presencial, nunca dispensa indicación remota
- **Convenios corporativos** activos con 12 empresas — agent puede mencionar si aplica al rol del usuario
- **Foto-control + escala VAS** documentado — agent debe usar como prueba objetiva ante escepticismo
- **CMP numbers** facilitadoras — agent puede compartir credenciales formales para personas adversariales
- **Discovery call para L4** — agent debe insistir en discovery 20 min, NO vender Plan Integral por DM
