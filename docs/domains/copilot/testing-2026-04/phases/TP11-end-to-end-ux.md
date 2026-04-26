# TP11 — End-to-End UX: "Feel like Claude Code"

**F# que valida:** síntesis de F0-F11. Heurísticas user-visible.
**Tiempo estimado:** 4-6 hs.
**Pre-req hard:** TP1-TP10 cerrados con findings + fixes aplicados.

---

## Misión

Validar que el copilot completo se SIENTE como Claude Code para marketing, no solo que cada componente teste OK aislado. Esta fase es la única que pesa heavy en juicio humano + Chrome DevTools live.

---

## Research mandate

Queries:

- `"claude code UX design principles 2026 agent feel"` — qué hace que Claude Code se sienta natural.
- `"conversational AI usability heuristic evaluation 2026"` — heurísticas Nielsen-style adaptadas a chat agents.
- `"streaming SSE UI perception latency under 1500ms 2026"` — perceptual thresholds.

---

## Heurísticas Claude Code (8 dimensiones)

| # | Heurística | Cómo se siente | Cómo se mide |
|---|---|---|---|
| H1 | **Inmediatez perceptual** | Respuesta empieza a renderear <1.5s sin importar la tarea. | Chrome DevTools network panel: TTFB block_start ≤1500ms en 100% turns. |
| H2 | **Planning visible** | En tareas grandes, ves el plan ANTES de la respuesta. | plan_card aparece ≤3s en multi-step. write_todos progresa visiblemente. |
| H3 | **Memoria viva** | El copilot recuerda lo que hablamos antes sin que se lo recuerdes. | Turn 7 referencia turn 2 sin re-prompt. Inspiraciones persisten. Brand siempre presente. |
| H4 | **Tono natural** | Suena humano, no robótico. Sin jerga técnica innecesaria. | Judge dim `tone` ≥4.0. 0 voseo. 0 phrases formula. |
| H5 | **Confianza con datos** | Cita métodos cuando aplica ("según StoryBrand…"). NO inventa números. | Citation accuracy ≥4.0. Faithfulness ≥0.85. |
| H6 | **Recuperación elegante** | Si algo falla, lo dice claro y ofrece next step. NO crashes silenciosos. | URL inválida / data missing / LLM timeout → mensaje claro + próximo paso. |
| H7 | **Output canal-aware** | "Para WhatsApp" devuelve algo que copia-pega real, sin markdown roto. | TP6 metrics: 16/16 outputs canal-correctos. |
| H8 | **Sin fricción cognitiva** | No te hace pensar dónde estás, qué hace, cómo seguir. Cards claras, status visible. | Manual: 5 user journeys reales sin necesidad de explicar al user qué pasa. |

---

## Scenarios — 5 user journeys reales

Cada journey = secuencia 5-10 turns que un user real haría. Browser Chrome DevTools por journey + screen recording opcional.

### J1 — "Soy nuevo, ayudame a configurar mi marca"

```
T1: hola, recién entro, ¿qué hago primero?
T2: <copilot propone setup brand minimal>
T3: <user acepta, pasos guiados>
...
T7: <brand creada, copilot sugiere offer next>
```

Heurísticas relevantes: H1, H2, H3, H4, H6, H8.
Tiempo total esperado: 3-5 min.

### J2 — "Tengo URL de competidor, quiero adaptar a mi marca"

```
T1: mirá esta landing: <url>
T2: <copilot fetch + propone inspiration_saved>
T3: ¿qué le robarías a ese estilo para mi marca?
T4: <copilot propuesta basada en brand_summary + URL>
T5: ahora armame copy para WhatsApp basado en esto
T6: <output WA correcto>
```

Heurísticas: H1, H3, H5, H7.

### J3 — "Tengo data, quiero entenderla"

```
T1: cuántas personas me escribieron esta semana
T2: <ask_tenant_data + número correcto>
T3: y comparado a la semana pasada?
T4: <comparative + insight>
T5: dame el top 3 ofertas por inscripciones
T6: <ranking + nombres reales>
```

Heurísticas: H1, H4, H5, H6.

### J4 — "Auditá mi marca y dame plan de mejora"

```
T1: audita mi marca completa, dame plan priorizado
T2: <plan_card aparece con write_todos visible>
T3: <copilot va completando todos uno por uno>
T4: <reporte final con 5 mejoras + priorización>
```

Heurísticas: H2, H3, H4, H5, H8.
Tiempo esperado: 1-2 min para plan + 2-3 min para reporte.

### J5 — "Pregunta sobre framework con citation"

```
T1: explícame el patrón hero/guide de StoryBrand para mi marca
T2: <copilot search KB + respuesta con citation a StoryBrand + adaptado a brand>
T3: dame ejemplos concretos para mi oferta de cocina
T4: <ejemplos contextuales con method aplicado>
```

Heurísticas: H3, H4, H5.

---

## Procedimiento por journey

Para cada J1-J5:

1. Browser Chrome DevTools session new.
2. Conversation new (clean slate).
3. Performance trace start (label J{N}).
4. Ejecutar turns en orden, esperando cada respuesta.
5. **Por cada turn**: capturar TTFB + latencia total + screenshot DOM final + console errors.
6. **Al cierre**: judge multi-dim sobre la última respuesta, `coherence` cross-turn, manual heurística check.
7. Performance trace stop → reportar TBT, LCP, INP.
8. Save trace + screenshots en `results/TP11-{fecha}/J{N}/`.

---

## Targets

| Heurística | Target |
|---|---|
| H1 inmediatez | TTFB ≤1500ms en 90% turns |
| H2 planning | plan_card ≤3s en multi-step |
| H3 memoria | turn N recuerda turn 1 en 5/5 journeys |
| H4 tono | judge `tone` avg ≥4.0 + 0 voseo |
| H5 confianza | judge `citation_accuracy` ≥4.0 + faithfulness ≥0.85 |
| H6 recuperación | 0 crashes silenciosos, mensaje claro 100% errores |
| H7 canal | 100% outputs WA/email/sms format-correctos |
| H8 fricción | manual review pass: "no tuviste que explicar" |

---

## Score final TP11

8 heurísticas × pass/fail = score X/8.

- **8/8** = el copilot SE SIENTE como Claude Code. Plan F0-F11 cumplió.
- **6-7/8** = está cerca. Documentar las 1-2 que faltan + plan de fix.
- **<6/8** = el redesign cumple a nivel código pero NO a nivel UX. Iteración mayor requerida.

---

## Failure playbook

Failures en TP11 suelen ser cross-componente. Por cada heurística que falla:

1. Identificar TP previo que la testeaba (ej. H4 → TP6).
2. Re-correr ese TP en isolation.
3. Si el TP previo pasa pero TP11 falla en heurística relacionada → **integration bug**: el componente funciona aislado pero no en flow completo.
4. Diagnose con trace_event: ¿faltan eventos? ¿latencia explota cuando se combinan tools?

Ejemplos integration-only bugs:

- H1 falla en J4 pero TP1 routing pasa → puede ser que en chains largas el system prompt cache se invalida.
- H3 falla en J2 turn 5 pero TP3 pasa standalone → inspiration podría no estar en contexto cuando hay también plan_card activo.

---

## Lo que necesito de Chris

- [ ] Tenant test "real" con todos los flujos cubiertos: brand_identity completo, ≥3 offers, ≥10 leads, ≥1 channel connection, brand_summary populated.
- [ ] (Opcional) screen recorder durante journeys para revisión human-in-the-loop.
- [ ] 30-60 min de Chris junto a la conversación durante J4 (audit) — heurística H8 requiere observación humana real.
