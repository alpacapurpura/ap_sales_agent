# Priorización — RICE / WSJF

> Solo cuando hay conflicto entre items. Si no, gut feeling + JTBD basta.

## RICE (Intercom)

```
Score = (Reach × Impact × Confidence) / Effort
```

| Variable | Cómo medir |
|---|---|
| **Reach** | Users impactados / período (ej: leads por mes) |
| **Impact** | 0.25 (mínimo) / 0.5 / 1.0 / 2.0 / 3.0 (massive) |
| **Confidence** | 100% (datos sólidos) / 80% / 50% (intuition) |
| **Effort** | Person-months estimados |

**Uso real:** comparar 2-3 alternativas. Score 2x diferencia = hay ganador. <50% = empate, decidí por gut.

## WSJF (SAFe)

```
WSJF = Cost of Delay / Job Size
```

```
Cost of Delay = Business Value + Time Criticality + Risk Reduction
```

Más simple que RICE para temas con time-pressure (ej: oportunidad de mercado que se cierra).

## Cuál usar

| Situación | Pick |
|---|---|
| Comparar features comparables | RICE |
| Time-criticality dispar (oportunidad mercado) | WSJF |
| Hay >5 items y solo elegimos top 3 | RICE |
| Decidiendo dentro de un PI | Gut + criterio JTBD primero |

## Antipatterns

- ❌ Score "matemático" como decisión final. Score = framework para conversación, no autoridad.
- ❌ Confidence siempre 100% (= sesgado).
- ❌ Effort calculado sin builder real involucrado.

## Reference

- Intercom RICE blog post (canónico).
- SAFe WSJF docs.
