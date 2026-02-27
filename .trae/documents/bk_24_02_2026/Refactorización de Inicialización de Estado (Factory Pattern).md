Tienes toda la razón. Usar un diccionario crudo en `routes.py` no es una buena práctica de Clean Code.

### Problema Detectado
Actualmente existe un **acoplamiento fuerte** y **lógica de negocio dispersa**.
1.  **Inconsistencia**: Si agregas un campo a `AgentState` (como acabamos de hacer con `active_strategy`), tienes que recordar agregarlo manualmente en `routes.py`. Si lo olvidas, el sistema puede fallar con `KeyError` o comportamientos inesperados.
2.  **Lógica en capa incorrecta**: La decisión de si el estado inicial es `RAPPORT` o viene de `active_enrollment.stage` es lógica de dominio, no debería estar en el controlador de la API.

### Solución Propuesta: Factory Method Pattern

Implementaré un patrón de fábrica para centralizar la creación del estado.

#### 1. Crear `create_initial_state` en `src/core/state.py`
Esta función actuará como constructor seguro.
- **Entradas**: Datos crudos (usuario, historial, enrollment).
- **Salida**: Un objeto `AgentState` completo y validado.
- **Responsabilidad**:
    - Inicializar todos los campos definidos en `TypedDict`.
    - Aplicar valores por defecto seguros (`None`, `False`, listas vacías).
    - Encapsular la lógica de "Recuperación de Estado" (decidir si empezamos en `Rapport` o restauramos sesión).

#### 2. Refactorizar `src/api/routes.py`
Limpiaré la función `process_message` para que delegue la creación del estado a esta nueva fábrica.
- El código pasará de tener un bloque de 15 líneas de lógica condicional de diccionarios a una sola llamada limpia:
  ```python
  initial_state = create_initial_state(
      user=user,
      incoming_msg=incoming,
      history=history,
      active_product=active_product,
      active_enrollment=active_enrollment,
      # ...
  )
  ```

### Beneficios
- **Mantenibilidad**: Si el `AgentState` cambia mañana, solo actualizamos el Factory en `state.py`. La API no se entera.
- **Robustez**: Garantizamos que ningún campo (como `financial_flag` o `disqualification_reason`) quede `undefined` al inicio del ciclo.

Procederé a implementar este cambio en `src/core/state.py` y luego actualizar `src/api/routes.py`.