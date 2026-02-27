Entendido. El modelo final queda así: **Únicamente los intentos de hackeo (Safety Violation) serán Semáforo Rojo**. Todo lo demás, incluyendo la descalificación, pasará por el Manager y el LLM (Semáforo Amarillo/Verde) para asegurar una gestión contextual y asertiva.

### 📋 Plan Definitivo

#### 1. Lógica de "Semáforo" en `node_router` (`src/core/nodes.py`)

* **🔴 Semáforo Rojo (Bypass LLM - Seguridad):**

  * **Trigger:** Solo activado por **Regex de Seguridad** (inyecciones de prompt, "actúa como", etc.).

  * **Acción:** Corta el flujo inmediatamente y devuelve una respuesta estática de rechazo.

* **🟢 Semáforo Verde (Manager + LLM - Negocio):**

  * **Trigger:** Todo lo demás (`disqualification_hard`, `agenda`, `medical`, `objections`, `sales`).

  * **Acción:** Detecta el `intent`, lo guarda en el estado y **pasa al** **`node_state_manager`**.

* <br />

