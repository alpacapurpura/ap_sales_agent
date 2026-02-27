# Visionarias Brain - Estructura de Proyecto (Agentes)

## 1. Módulos y Agentes

### Ubicación de Agentes
-   **Ruta Base**: `backend/src/modules/*/application/agents/`
-   **Convención**: Cada módulo puede tener su propio conjunto de agentes.

### Módulos Principales
| Módulo | Ruta | Descripción |
|---|---|---|
| **Marketing** | `src/modules/marketing/` | Gestión de Clientes, Segmentación, Identidad. |
| **Sales** | `src/modules/sales/` | Gestión de Oportunidades, Closer, Calificación. |
| **Communication** | `src/modules/communication/` | Orquestación, Canales (Telegram, WhatsApp), Mensajería. |
| **IAM** | `src/modules/iam/` | Gestión de Tenants, Autenticación. |
| **Brand** | `src/modules/brand/` | Gestión de Marca, Identidad Visual. |

## 2. Componentes Clave

### Sales (Agentes de Venta)
-   **Nodos**: `src/modules/sales/application/agents/nodes.py` (Lógica de decisión).
-   **Grafos**: `src/modules/sales/application/agents/graph.py` (Definición de flujo LangGraph).
-   **Prompts**: `src/modules/sales/application/agents/prompts.py` (Instrucciones LLM).
-   **Modelos**: `src/modules/sales/infrastructure/models/lead_model.py`.
-   **Repositorios**: `src/modules/sales/infrastructure/lead.py`.

### Marketing (Agentes de Identidad)
-   **Servicios**: `src/modules/marketing/application/services/identity_service.py`.
-   **Modelos**: `src/modules/marketing/infrastructure/models/customer.py`.
-   **Repositorios**: `src/modules/marketing/infrastructure/repositories/customer_repository.py`.

### Communication (Orquestación)
-   **Orquestadores**: `src/modules/communication/application/orchestrators/chat.py`.
-   **Canales**: `src/modules/integration/infrastructure/channels/`.

## 3. Reglas de Modificación
1.  **Agentes Nuevos**:
    -   Crear en `src/modules/{module}/application/agents/`.
    -   Seguir patrón: `nodes.py`, `graph.py`, `prompts.py`.
    -   Registrar en `graph.py` del módulo.

2.  **Modificación de Flujo**:
    -   Editar `graph.py` para cambiar transiciones.
    -   Editar `nodes.py` para cambiar lógica de decisión.

3.  **Integración**:
    -   NUNCA importar modelos de infraestructura directamente en agentes.
    -   Usar interfaces de Repositorio o Servicios de Dominio.
