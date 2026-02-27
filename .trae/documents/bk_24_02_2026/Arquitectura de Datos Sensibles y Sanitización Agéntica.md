# Arquitectura de "Safety Layer" para Datos Sensibles

Entendido. Como arquitecto de software, te propongo una solución robusta y escalable que evoluciona el nodo "financial" (ahora obsoleto) a una verdadera **Capa de Seguridad ("Safety Layer")**.

## 🛡️ Análisis Estratégico y Mejores Prácticas

En sistemas agénticos conversacionales, confiar únicamente en un LLM para sanitizar datos es arriesgado (alucinaciones, omisiones). Las mejores prácticas (NIST AI RMF, OWASP for LLM) sugieren un enfoque de **Defensa en Profundidad**:

1.  **Detección Determinista (Regex/Keywords):** Rápida y precisa para patrones conocidos (tarjetas de crédito, emails, teléfonos, palabras clave de la empresa).
2.  **Detección Semántica (LLM "Vigilante"):** Para entender el contexto ("mi clave es..." vs "la clave del éxito es...").
3.  **Auditoría de Fuga (Leakage Audit):** Registrar si el modelo intentó revelar algo indebido, incluso si fue bloqueado.

No necesitamos reinventar la rueda, pero sí adaptarla a tu dominio.

## 🏗️ Propuesta de Solución

### 1. Modelo de Datos: `SensitiveData`
Crearemos una tabla en PostgreSQL para gestionar dinámicamente qué es "sensible". Esto permite que desde el Admin Panel tú (o el cliente) agreguen nuevas reglas sin tocar código.

*   **Tabla:** `sensitive_data`
*   **Campos:**
    *   `category`: "financial", "pii", "business_secret", "system_prompt".
    *   `pattern`: Regex o palabra clave.
    *   `replacement`: Texto de reemplazo (ej: `[REDACTED]`, `[PRECIO_CONSULTAR]`).
    *   `is_active`: Boolean.
    *   `context_instruction`: Instrucción para el LLM (opcional).

### 2. Nuevo Nodo: `safety_layer`
Reemplazaremos el nodo `financial` por `safety_layer`. Este nodo será el "Portero Final".

**Flujo del Nodo:**
1.  **Entrada:** Recibe el mensaje generado por el nodo `generator`.
2.  **Paso 1: Escaneo Rápido (Regex):** Busca coincidencias con la tabla `SensitiveData`. Si encuentra algo crítico (ej. tarjeta de crédito), lo redacta inmediatamente.
3.  **Paso 2: Verificación Contextual (LLM Ligero):** Si hay dudas o si la política lo requiere, un modelo rápido (GPT-3.5/Flash) verifica si el texto revela secretos de negocio definidos en la DB.
4.  **Salida:** Mensaje sanitizado.
5.  **Side Effect:** Si se detectó una filtración, se marca en el `AgentState` (`safety_flag: true`) para auditoría futura.

### 3. Gestión desde Admin UI
Añadiremos una vista en Streamlit para gestionar estas reglas, permitiéndote diferenciar entre "Datos del Producto" (Precios, Fechas) y "Secretos de Empresa" (Márgenes, Nombres de socios).

## 📝 Plan de Implementación

1.  **Base de Datos:** Crear modelo `SensitiveData` en `src/services/db/models/business.py`.
2.  **Servicio de Seguridad:** Crear `src/services/safety_service.py` que encapsule la lógica de detección (Regex + LLM).
3.  **Refactorización del Grafo:**
    *   Renombrar nodo `financial` a `safety_layer` en `src/core/nodes.py`.
    *   Actualizar `src/core/agent.py` para usar el nuevo nombre.
4.  **Admin UI:** Actualizar `src/admin/app.py` para incluir el gestor de datos sensibles.

Esta arquitectura cumple con tu requisito de **seguridad, mantenibilidad y escalabilidad**, alejándonos de los `if`s hardcodeados y moviéndonos a una configuración gobernada por datos.
