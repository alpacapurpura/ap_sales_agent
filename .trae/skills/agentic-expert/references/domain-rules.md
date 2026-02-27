# Visionarias Brain - Reglas de Dominio (Agentes)

## 1. Identidad vs Contexto de Venta
Regla Fundamental: **Separación de Responsabilidades**

### Reglas de Arquitectura DDD para la IA:
1. STRICT BOUNDARIES: El módulo `sales` NUNCA debe importar NADA de `integration` o de APIs de mensajería (Telegram, WhatsApp).
2. DEPENDENCY INVERSION: `integration` depende de `communication` (para enviarle los webhooks procesados), NUNCA al revés.
3. CHANNEL AGNOSTIC: Los Prompts y Agentes en `sales` no deben hacer referencias directas a elementos de UI o canales específicos. Hablan en texto plano o Markdown genérico.
4. SHARED KERNEL: En `src/shared` solo van interfaces, clientes LLM base (OpenAI wrapper) y utilidades puras. NINGUNA lógica de negocio (Lead, Customer, Ofertas) debe vivir en `shared`.


### Marketing (Identidad)
-   **Entidad Maestra**: `CustomerProfile`
-   **Ubicación**: `src/modules/marketing/domain/customer.py`
-   **Responsabilidad**: Fuente única de verdad para la identidad del usuario.
-   **Campos Exclusivos**: `full_name`, `email`, `phone`, `telegram_id`, `whatsapp_id`.
-   **Prohibición**: Ningún otro módulo debe almacenar datos de contacto primarios. Deben referenciar `customer_id`.

### Sales (Contexto)
-   **Entidad Transaccional**: `Lead`
-   **Ubicación**: `src/modules/sales/domain/lead.py`
-   **Responsabilidad**: Gestionar el estado de la negociación y el "calor" del cliente.
-   **Relación**: `Lead` tiene un `customer_id` (FK lógica) que apunta a `CustomerProfile`.
-   **Prohibición**: No agregar campos como `email` o `phone` al modelo `Lead`. Si se necesita el email, se consulta al `CustomerRepository` usando el `customer_id`.

## 2. Flujo de Comunicación
Regla Fundamental: **Orquestación Centralizada**

### Entrada (Input)
-   **No Webhooks Directos**: Los agentes NUNCA deben exponer endpoints de webhook directamente.
-   **Orquestador**: `ChatOrchestrator` (`src/modules/communication/application/orchestrators/chat.py`) es el único punto de entrada a la lógica conversacional.
-   **Responsabilidad de los Módulos en la Entrada**:
    1.  `integration`: Recibe el webhook HTTP en crudo de la API externa (Meta/Telegram), valida tokens, extrae el texto y lo convierte a un objeto `GenericInboundMessage`.
    2.  `communication` (Orquestador): Recibe el `GenericInboundMessage` limpio de `integration`.
    3.  `communication`: Resuelve identidad (buscar/crear `CustomerProfile` vía `IdentityService`).
    4.  `communication`: Resuelve contexto (buscar/crear `Lead` activo).
    5.  `communication`: Invoca al Agente de `sales` con un `AgentState` enriquecido.

### Estado del Agente (AgentState)
-   Los agentes reciben un estado ya poblado.
-   **Schema**:
    ```python
    class AgentState(TypedDict):
        messages: List[BaseMessage]
        user_id: str          # ID del Lead (Contexto)
        customer_id: str      # ID del Customer (Identidad)
        user_profile: Dict    # Datos de Marketing (Nombre, Intereses)
        active_product: Any   # Producto en lanzamiento
    ```
### Salida (Output)
-   **No Envío Directo**: Los agentes NUNCA deben llamar a APIs como `telegram_api.send_message` directamente.
-   **Retorno de Estado**: El agente debe limitarse a generar su respuesta y añadirla a la lista `messages` del estado.
-   **Responsabilidad en la Salida**: 
    1. El Orquestador (`communication`) lee la nueva respuesta del agente generada en el grafo.
    2. El Orquestador delega el envío físico al módulo `integration` (ej. llamando a una interfaz o publicando un evento que `integration` escucha), pasándole el texto y el ID del canal.

