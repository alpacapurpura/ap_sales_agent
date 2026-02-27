# Plan de Mejora: Arquitectura Multiproducto y Ventanas de Lanzamiento

## 1. Actualización de `AgentState` (src/core/state.py)
Añadiremos contexto explícito del producto en la memoria del agente para evitar ambigüedades.
- Agregar campo `product_id: Optional[str]`.
- Agregar campo `launch_stage: Literal["pre_launch", "open_cart", "close_cart", "evergreen"]` para adaptar el tono de urgencia.

## 2. Lógica de Selección de Producto Inteligente (src/services/repository.py)
Reemplazar la búsqueda simple `get_active_product` por una lógica de negocio real.
- **Nuevo Método:** `get_current_launch_product()`
- **Lógica:**
  1. Filtrar productos con `status='active'`.
  2. Leer campo JSON `dates` (`start`, `offer_deadline`).
  3. Comparar con `datetime.now()`.
  4. Retornar el producto que esté "En Vivo" (dentro de fechas).
  5. Si hay varios, priorizar el High Ticket sobre Low Ticket, o el que cierre antes (Urgencia).

## 3. Integración en Flujo (src/api/routes.py)
Actualizar la inyección de contexto inicial.
- Usar el nuevo método `get_current_launch_product()`.
- Inyectar `product_id` y `launch_stage` en el `initial_state`.
- Esto permitirá que los nodos futuros (ej. `node_pitch`) sepan si deben usar "cierre por escasez" (si `close_cart`) o "educación" (si `pre_launch`).

## 4. Verificación
- Simularemos un producto con fecha de cierre "ayer" y verificaremos que NO sea seleccionado.
- Simularemos un producto con fecha "mañana" y verificaremos que SÍ sea seleccionado.
