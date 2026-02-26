# Arquitectura Técnica: Sistema Agentic "Visionarias" (Pure Python & Dockerized)

Esta es la versión mejorada y "Code-First" de la arquitectura. Hemos eliminado la dependencia de n8n para centralizar todo el control lógico, la seguridad y el manejo de errores en una única aplicación Python robusta. Esto reduce la latencia, simplifica el despliegue y mejora la mantenibilidad.

## 1. Stack Tecnológico (100% Python)

Abandonamos el enfoque híbrido (n8n + Python) por un enfoque monolítico modular en Python.

*   **API Gateway & Webhook Handler**: `FastAPI` (Python 3.11+). Maneja directamente la verificación de webhooks de WhatsApp (Meta Graph API), validación de firmas de seguridad (X-Hub-Signature) y el enrutamiento de mensajes.
*   **Orquestación Cognitiva**: `LangGraph`. Define la máquina de estados (S1 -> S6) de forma determinista.
*   **Memoria & Estado**: `Redis`. Almacenamiento de `checkpoint` de LangGraph (persistencia del hilo de conversación) y datos de sesión volátiles.
*   **Base de Conocimiento (RAG)**: `Qdrant`. Búsqueda vectorial híbrida (semántica + keyword).
*   **Telemetría y Logs**: `PostgreSQL`. Almacenamiento estructurado de cada interacción para futuros análisis y entrenamiento (RLHF).
*   **Proxy Inverso**: `Traefik`. Gestión de certificados SSL y enrutamiento en producción.

## 2. Diagrama de Flujo de Datos

```mermaid
graph TD
    User((Usuario WhatsApp)) -->|Mensaje| Traefik[Traefik (Reverse Proxy)]
    Traefik -->|Forward| API[FastAPI (Python App)]
    
    subgraph "Visionarias Brain (Python)"
        API -->|1. Validate & Extract| WH[Webhook Handler]
        WH -->|2. Load State| Redis[(Redis)]
        WH -->|3. Invoke Graph| Agent[LangGraph Agent]
        
        Agent -->|4. Retrieve Context| Qdrant[(Qdrant)]
        Agent -->|5. Generate| LLM[LLM (GPT-4o)]
        Agent -->|6. Log Telemetry| DB[(PostgreSQL)]
    end
    
    Agent -->|7. Send Reply| WA_API[Meta WhatsApp API]
    WA_API -->|8. Deliver| User
```

## 3. Estructura del Grafo (LangGraph) Mejorada

El grafo gestiona no solo la conversación, sino también lógica de negocio que antes hacía n8n.

*   **Node: `entry_point`**: 
    *   Verifica tiempo desde último mensaje (lógica de sesión expirada > 6h).
    *   Si es nueva sesión, resetea estado pero mantiene perfil de usuario.
*   **Node: `guardrails`**:
    *   Filtros de seguridad y ética.
    *   Detección de intentos de manipulación de prompt.
*   **Node: `intent_classifier`**:
    *   Clasifica: `info_product`, `pricing`, `objection`, `closing`, `human_handoff`.
*   **Node: `state_manager`**:
    *   Máquina de estados finitos (S1..S6). Transiciones estrictas.
*   **Node: `rag_retrieval`**:
    *   Búsqueda contextual en Qdrant según el estado actual.
*   **Node: `response_synthesis`**:
    *   Generación de respuesta con personalidad "Visionaria".
*   **Node: `financial_enforcer`**:
    *   Sobrescribe CUALQUIER número generado por el LLM con datos duros de la base de datos de productos. Garantía de "Cero Alucinaciones de Precios".

## 4. Infraestructura Dockerizada (Development vs Production)

Usaremos Docker Compose con perfiles para separar entornos.

### Servicios
1.  **app**: La aplicación Python (FastAPI + LangGraph).
2.  **redis**: Persistencia de sesiones.
3.  **qdrant**: Base de datos vectorial.
4.  **postgres**: Logs y analítica.
5.  **traefik**: Solo en perfil `production`.

### Configuración de Red
*   **Development**: Puertos expuestos localmente (8000, 6379, 5432).
*   **Production**: Solo Traefik expone puertos (80, 443). La app se comunica solo dentro de la red interna Docker.

## 5. Implementación de Calidad (Best Practices)

1.  **Tipado Estricto**: Uso intensivo de Pydantic para validar entradas y salidas del LLM.
2.  **Testing**: Tests unitarios para los nodos del grafo (simular estados).
3.  **Manejo de Errores**: Si el LLM falla o tarda, fallback a mensajes predefinidos seguros.
4.  **Async/Await**: Todo el stack es asíncrono para manejar alta concurrencia de mensajes de WhatsApp.
