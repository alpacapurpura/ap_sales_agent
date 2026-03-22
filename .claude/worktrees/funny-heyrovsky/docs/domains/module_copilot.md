---
module: Copilot
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
- Acompañar al Dueño del Negocio como un asistente flotante (similar a Cursor) por toda la interfaz. Ayuda a llenar configuración, crear currículas, e inyectar estilos usando LangGraph.

## 2. Reglas de Negocio Estrictas (Business Rules)
- Mantiene un estado de sesión totalmente aislado del sales_agent. Su objetivo es configurar y estructurar el sistema SaaS, no vender.
- Utiliza invocación de herramientas (Function Calling/MCP) de forma estricta para leer y escribir sobre los formularios de los otros dominios (ej. crear productos en el módulo offer).

## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/modules/copilot/
- Frontend: (Componente global de chat flotante, por definir).

## 4. Casos Borde Conocidos (Edge Cases)
- Bloqueos de Web Scraping: Fallo del extractor interno cuando intenta escanear la web actual del cliente y se topa con un muro Cloudflare o un 403 Forbidden.
- Alucinación de Campos Estrictos: El modelo intentando enviar strings de texto a campos Enum o numéricos estables (Pydantic Validation Error) al tratar de autocompletar un formulario.