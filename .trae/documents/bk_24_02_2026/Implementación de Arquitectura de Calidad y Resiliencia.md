# Arquitectura de Calidad y Resiliencia (Plan de Acción)

Como arquitecto de software, te explico que estas recomendaciones **NO** implican actualizar los "skills" o "rules" de Trae (la IA). Son **mejoras técnicas en tu código e infraestructura** que debemos programar e integrar en el proyecto.

Actualmente, tu proyecto carece de mecanismos automatizados para prevenir errores de estructura (como los imports rotos) y para que Docker sepa cuándo reiniciar un servicio automáticamente.

## 1. ¿Por qué necesitamos esto?

*   **Linting Estricto (Ruff):** Es un "corrector ortográfico" para código. Detecta imports no usados, errores de sintaxis y referencias a archivos inexistentes *antes* de que intentes ejecutar el servidor. Nos hubiera avisado de los errores de importación inmediatamente.
*   **Docker Healthcheck:** Es un "monitor de pulso". Docker le preguntará periódicamente a tu API "¿Estás viva?". Si la API no responde (como pasó con el timeout), Docker la reiniciará automáticamente para intentar recuperarla sin intervención humana.

## 2. Plan de Implementación

Vamos a realizar cambios en 3 archivos clave:

### A. Configuración de Linting (`backend/pyproject.toml`)
Crearemos este archivo (que no existe) para configurar `ruff`. Es el estándar moderno para configuración de herramientas Python.
*   **Acción:** Crear `backend/pyproject.toml` con reglas para detectar imports rotos (`F401`, `E402`) y errores de sintaxis.

### B. Dependencias (`backend/requirements.txt`)
Añadiremos `ruff` a las dependencias para que esté disponible en el entorno de desarrollo y CI/CD.
*   **Acción:** Añadir `ruff>=0.3.0` a `requirements.txt`.

### C. Resiliencia (`backend/Dockerfile`)
Añadiremos la instrucción `HEALTHCHECK` al contenedor. Usará `curl` (que ya instalamos) para llamar a `/health`.
*   **Acción:** Añadir bloque `HEALTHCHECK` en el `Dockerfile`.

## 3. Pasos de Ejecución

1.  **Instalar Ruff:** Añadir `ruff` a `backend/requirements.txt`.
2.  **Configurar Ruff:** Crear `backend/pyproject.toml` con la configuración base.
3.  **Implementar Healthcheck:** Modificar `backend/Dockerfile` para incluir el healthcheck nativo.
4.  **Validación:** Ejecutar el linter sobre el código actual para ver si detecta algo más y reconstruir el contenedor para activar el healthcheck.

Este plan elevará la madurez de tu proyecto de "prototipo funcional" a "sistema robusto". ¿Procedemos?
