# Diseño de Perfil de Usuario "Valeria" y Estrategia de Captura de Datos

## 1. Estructura de Datos (Schema)

Centralizaremos la definición de los datos en `src/core/schema.py` usando Pydantic. Esto nos da validación de tipos y estructura clara.

### Clasificación de Datos

Dividiremos los datos en tres niveles de prioridad para guiar al agente:

1. **MANDATORY (Criticos para Calificación)**: Sin esto no podemos avanzar a la oferta.

   * `business_stage`: \[ACTIVE, IDEA, NONE]. Filtro duro.

   * `financial_tier`: \[HIGH, MEDIUM, LOW]. Filtro de capacidad de pago.
2. **DESIRABLE (Estratégicos para Venta)**: Necesarios para personalizar el pitch (Nodos S3/S4).

   * `pain_point`: El dolor principal (Burnout, Caos, Ventas Bajas).

   * `goal`: El deseo principal (Libertad, Escalar, Orden).

   * `decision_maker`: \[SOLO, PARTNER]. Para manejar objeciones.
3. **OPTIONAL (Contexto/Rapport)**: Se llenan si surgen naturalmente.

   * `name`: Nombre.

   * `occupation`: Profesión exacta.

   * `location`: Ciudad/País.

## 2. Implementación Técnica

### A. Actualización de `src/core/schema.py`

Crearemos los Enums y el modelo `UserProfile` que unificará `psychographics` y `demographics`.

```python
class UserProfile(BaseModel):
    # --- Identidad (Opcional) ---
    name: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    
    # --- Calificación (Mandatory) ---
    business_stage: Optional[BusinessStage] = None  # Enum: ACTIVE, IDEA, NONE
    financial_tier: Optional[FinancialTier] = None  # Enum: SURVIVAL, COMFORT, SCALING
    
    # --- Psicografía (Desirable) ---
    main_pain_point: Optional[str] = None
    main_goal: Optional[str] = None
    decision_maker: Optional[DecisionMaker] = None # Enum: SOLO, PARTNER
    
    # --- Metadata de Progreso ---
    missing_fields: List[str] = [] # Para que el Agente sepa qué falta preguntar
```

### B. Estrategia de Prompting (`state_transition.j2`)

Modificaremos el prompt del **Manager** para que actúe como un "cazador de datos" pasivo.

* **Instrucción**: "Analiza la conversación y extrae cualquier dato nuevo."

* **Lógica de Siguiente Paso**: "Si falta un dato MANDATORY y estamos en etapa de Discovery, tu estrategia es preguntarlo sutilmente."

### C. Persistencia en `src/core/nodes.py`

En el nodo `manager`:

1. El LLM devuelve un JSON con `extracted_info`.
2. Actualizamos el `state["user_profile"]`.
3. Calculamos dinámicamente qué campos faltan (`missing_fields`) y lo inyectamos de vuelta al estado para que el LLM lo sepa en el siguiente turno.

## 3. Plan de Ejecución

1. **Refactorizar** **`src/core/schema.py`**: Añadir Enums y `UserProfile`.
2. **Actualizar** **`src/core/state.py`**: Cambiar el tipo de `user_profile` en `AgentState`.
3. **Actualizar** **`src/core/prompts/templates/state_transition.j2`**:

   * Inyectar la definición de campos.

   * Instruir al modelo para llenar los huecos.
4. **Actualizar** **`src/core/nodes.py`**:

   * Lógica de fusión (merge) de datos nuevos con existentes.

   * Cálculo de campos faltantes.

