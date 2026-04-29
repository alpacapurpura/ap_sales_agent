# Opportunity Solution Tree (Torres)

> Continuous Discovery Habits — Teresa Torres. SSoT para mapeo problema→solución.

## Estructura

```
            [Desired Outcome]            ← métrica norte estrella o sub-outcome
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
  [Opp 1]    [Opp 2]    [Opp 3]         ← problemas/dolores user (NO soluciones)
     │          │
   ┌─┴─┐      ┌─┴─┐
   ▼   ▼      ▼   ▼
 [SolA][SolB][SolC][SolD]                ← múltiples soluciones por opportunity
   │     │     │     │
   ▼     ▼     ▼     ▼
[Exp1][Exp2][Exp3][Exp4]                 ← experimentos baratos validar
```

## Reglas de oro

1. **Empieza por outcome, no por idea.** "Aumentar tasa de activación" antes de "agregar onboarding tour".
2. **Opportunity ≠ Solution.** Opp = dolor user. Sol = qué construyes. Confundirlos = comprometerse antes de validar.
3. **Múltiples soluciones por opp.** Mínimo 2-3 alternativas. Mata el "wall of features".
4. **Experimento ANTES de construir.** Si la solución cuesta 4 semanas, gasta 2 días validando.
5. **Visualiza el árbol.** En `opportunities/{slug}.md` documentas cada nodo. Backbone visual en `INDEX.md` o pizarra.

## Cómo usarlo en `/pm`

| Etapa | Acción PM |
|---|---|
| Captura señal | "Vi que X pasa". → `opportunities/{slug}.md` con problem statement |
| Validar | Recolectar evidencia (entrevistas, datos, observación). Tamaño (reach, frecuencia, severidad). |
| Generar soluciones | Mínimo 2. Evita primera idea = idea ganadora. Usa "10 maneras de resolver esto". |
| Priorizar | RICE per solución. Confidence más bajo = más experimento, menos build. |
| Experimentar | Smoke test, fake door, mockup test, prototype. Métrica clara. |
| Promover | Si solución validada + outcome alineado → asciende a PI. |

## Antipatterns

- ❌ Una sola solución por opportunity (= falsa elección)
- ❌ Solución sin opportunity ("queremos hacer X feature porque sí")
- ❌ Skip experimentos en soluciones de >2 semanas
- ❌ Outcome vago ("mejorar UX")

## Reference

Torres, T. (2021). *Continuous Discovery Habits*.
