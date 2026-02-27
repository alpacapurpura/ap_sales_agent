# Communication Module Documentation Spec

## Why
El usuario necesita asegurar que el conocimiento sobre la responsabilidad del módulo `communication` (como punto central de conexiones, integraciones y canales) no se pierda. Se requiere una forma de documentación "en el código" que sea visible y mantenible, evitando documentos externos obsoletos.

## What Changes
- **Crear `backend/src/modules/communication/README.md`**: Un archivo específico dentro del módulo que explique su Bounded Context, responsabilidades, y qué integraciones viven ahí.
- **Actualizar `backend/README.md`**: Agregar una sección de "Mapa de Módulos" que defina brevemente la responsabilidad de cada módulo principal (`communication`, `sales`, `landing`, `offer`, etc.) para dar contexto global.
- **Agregar Docstring en `backend/src/modules/communication/__init__.py`**: Documentación a nivel de código Python para que herramientas de IDE y autocompletado muestren el propósito del paquete.

## Impact
- **Affected specs**: Ninguna funcional. Solo documentación.
- **Affected code**: `backend/src/modules/communication/__init__.py` y nuevos archivos markdown.

## ADDED Requirements
### Requirement: Module Documentation
El módulo `communication` DEBE tener un `README.md` que detalle:
- **Propósito**: Centralizar la comunicación omnicanal con leads/clientes.
- **Integraciones Soportadas**: WhatsApp, Telegram, Gmail, Calendar, Webhooks.
- **Principios**: Aislamiento de proveedores externos, normalización de mensajes.

### Requirement: Global Architecture Map
El `README.md` raíz del backend DEBE listar los módulos de alto nivel y su responsabilidad única para guiar a futuros desarrolladores.

## MODIFIED Requirements
### Requirement: Python Package Docstring
El archivo `__init__.py` del módulo communication debe tener un docstring explicativo.
