---
module: Technical Module Core
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
- Centralizar la infraestructura técnica base de la aplicación. Es 100% agnóstico al negocio. Contiene la configuración de base de datos (database.py), carga de variables de entorno (config.py), capas de seguridad y formato de logs.

## 2. Reglas de Negocio Estrictas (Business Rules)
- Aislamiento Total: core NO DEBE importar NADA de la carpeta shared ni de los módulos de negocio (modules). Nunca debe conocer reglas de dominio, nombres de tablas lógicas o modelos.

## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/core/

## 4. Casos Borde Conocidos (Edge Cases)
- Variables Faltantes: Cambios en la validación del entorno que causan fallos silenciosos si el archivo .env no está debidamente sincronizado en los despliegues.