# Jobs-to-be-Done (JTBD)

> Christensen / Ulwick. User no compra producto, contrata "trabajo". Antes definir feature → entendé el job real.

## Forma canónica

> **Cuando** {situación}, **quiero** {motivación}, **para que** {resultado esperado}.

Ejemplo: "Cuando un lead pregunta por mi servicio fuera de horario, quiero que algo le responda profesionalmente, para que no se enfríe antes de que pueda contactarlo."

## Niveles del job

| Nivel | Pregunta |
|---|---|
| **Functional** | ¿Qué tarea ejecuta? (responder leads) |
| **Emotional** | ¿Cómo quiere sentirse? (tranquilo, en control) |
| **Social** | ¿Cómo quiere ser percibido? (profesional, escalado) |

PRs robustos atienden los 3 niveles, no solo functional.

## Forces of progress (Klement)

User cambia de "lo que hace hoy" a "tu producto" cuando:

```
[Push of situation]  +  [Pull of new solution]
       >
[Anxiety of new]  +  [Habit of present]
```

PM identifica los 4 elementos antes de comprometer feature. Si el habit/anxiety dominan, ningún feature lo arregla — necesita educación / onboarding / cambio modelo.

## Outcome statements (Ulwick)

Forma medible JTBD:
> **Minimizar/Maximizar** {métrica}, **cuando** {contexto}.

Ejemplo: "Minimizar el tiempo desde que un lead pregunta hasta que recibe respuesta, cuando el dueño no está disponible."

## Cómo usarlo en `/pm`

| Etapa | Acción |
|---|---|
| Discovery inicial | Preguntá al user: "Si eliminás el feature, ¿qué deja de funcionar para vos?" |
| Definir PR | Empezá con JTBD en formato canónico. Sin JTBD = no PR. |
| Validar solución | Cada solución candidata debe responder al JTBD. Si no, descarte. |
| Métrica outcome | Derivar de outcome statement. |

## Antipatterns

- ❌ Confundir feature con job. "User quiere campo X" — ¿qué job hace ese campo?
- ❌ JTBD genérico ("quiero ahorrar tiempo") — usable para cualquier producto = inservible.
- ❌ Saltar al "cómo" antes del "por qué".

## Reference

- Christensen, C. *Competing Against Luck*.
- Ulwick, A. *Jobs to be Done: Theory to Practice*.
- Klement, A. *When Coffee and Kale Compete*.
