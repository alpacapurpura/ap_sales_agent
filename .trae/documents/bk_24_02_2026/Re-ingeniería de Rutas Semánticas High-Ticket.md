# Propuesta Técnica: Re-ingeniería de Rutas Semánticas High-Ticket

Esta propuesta integra tu excelente estrategia de "Semáforo" con nuestra arquitectura actual en `LangGraph` y `FastEmbed`.

## 1. Estrategia de Enrutamiento (Traffic Light System)

He analizado tu propuesta y es **técnicamente superior** a la actual para un producto High-Ticket porque prioriza la *protección del tiempo* y la *consistencia financiera* sobre la flexibilidad del LLM.

### Cambios Clave:

1. **Semáforo Rojo (Bloqueo)**: Detección inmediata de clientes no cualificados (`disqualification_hard`) -> Salida rápida sin gastar tokens de "venta".
2. **Semáforo Amarillo (Defensa)**: Detección de condiciones de agenda innegociables (`agenda_defense`) -> Script de autoridad ("Micro-compromiso").
3. **Semáforo Naranja (Objeciones Críticas)**: Manejo quirúrgico de dinero y socios (`objection_financial`, `objection_partner`) -> Scripts probados, sin alucinaciones.
4. **Semáforo Verde (Venta)**: Solo aquí permitimos que el LLM use su "magia" empática (`intent_pain_explore`).

## 2. Plan de Implementación

### Paso 1: Actualizar `src/services/router_service.py`

Reemplazaré el diccionario `_routes` actual con tu nueva estructura categorizada.

* **Mejora Propuesta**: Usaré **umbrales dinámicos**.

  * `0.82` para **Filtros Duros** (Agenda/Descalificación) para evitar falsos positivos (no ofender a un cliente válido).

  * `0.76` para **Objeciones** (Financiera/Socio), ya que los clientes suelen ser sutiles al hablar de dinero ("estoy ajustada", "mi marido dice...") y preferimos detectar de más a perder la oportunidad de rebatir.

### Paso 2: Refactorizar `src/core/nodes.py`

Modificaré `node_router` para implementar la lógica de decisión exacta que propusiste:

```python
# Lógica "Traffic Light"
if intent == "disqualification_hard":
    return "hard_exit_flow"  # Cierre inmediato
elif intent == "agenda_defense":
    return "agenda_enforcement_flow"  # Protocolo de autoridad
elif intent in ["objection_financial", "objection_partner", "risk_guarantee"]:
    return "critical_script_handler"  # Script exacto
# ... resto del flujo
```

###
