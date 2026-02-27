Esta es una excelente pregunta de arquitectura. Como Backend Senior, te daré mi evaluación técnica directa sobre tu implementación actual vs. Middleware en el contexto de **FastAPI**.

### **Veredicto Rápido: Tu implementación actual es la correcta.**
No cambies a Middleware global para esto. Lo que tienes ahora (Dependency Injection con `Depends`) es la **"Best Practice"** idiomática en FastAPI para manejo de autenticación y multi-tenancy.

---

### **Análisis Técnico: ¿Por qué NO usar Middleware aquí?**

A diferencia de frameworks antiguos (como Express.js o Django) donde el Middleware era la única forma de interceptar peticiones, en FastAPI el sistema de Inyección de Dependencias es superior para lógica de negocio por estas razones:

1.  **Granularidad y Control (El problema del "Martillo")**
    *   **Middleware:** Es un martillo gigante. Se ejecuta en **todas** las peticiones, incluso en `/health`, `/docs`, `OPTIONS` (CORS), o `/webhooks`.
    *   *El Riesgo:* Si pones la lógica de Tenant en un middleware, tendrías que llenar tu código de excepciones: *"Si la ruta es /webhook, ignora el tenant... Si es /health, ignora..."*. Eso se vuelve "código espagueti" propenso a errores.
    *   **Tu Código Actual:** Aplicas `dependencies=[Depends(get_tenant_context)]` **solo** a los routers que manejan datos sensibles (`/admin`, `/products`). Dejas libres a `/webhook` y `/health`. Esto es limpio, explícito y seguro.

2.  **Manejo de Errores y Contexto**
    *   En FastAPI, las dependencias (`Depends`) se integran nativamente con el sistema de excepciones (`HTTPException`). Si el token falla, FastAPI devuelve un 401/403 limpio y documentado automáticamente.
    *   Los Middlewares operan "fuera" del contexto de validación de pydantic/FastAPI, lo que hace más difícil devolver respuestas de error estructuradas o inyectar el usuario autenticado directamente en la función del controlador.

3.  **Documentación Automática (OpenAPI/Swagger)**
    *   Al usar `Depends`, FastAPI sabe que esos endpoints requieren autenticación y automáticamente pone el candadito 🔒 en el Swagger UI. Con Middleware, Swagger no se entera y tendrías que documentarlo manualmente.

### **¿Cuándo SÍ usar Middleware?**
Tu proyecto **ya usa** middleware para lo que realmente sirve:
*   **Logging (`logging_middleware`):** Quieres loguear *todo*, incluso los errores 500 o las rutas no encontradas.
*   **CORS (`CORSMiddleware`):** Necesitas headers en *todas* las respuestas.

### **Conclusión Senior**
Tu arquitectura actual es sólida y escalable.
*   **No inventes problemas:** Pasar a Middleware para esto sería un paso atrás (over-engineering y pérdida de flexibilidad).
*   **Mejora sugerida (Opcional):** Lo único que podrías refinar a futuro es encapsular la lógica de `get_tenant_context` en una clase `TenantService` si la lógica de resolución se vuelve muy compleja (ej. buscar en caché Redis antes que en DB), pero la *forma* de llamarlo (vía `Depends`) debe mantenerse.

**Resumen:** Estás siguiendo el patrón de diseño correcto para FastAPI. No cambies nada en este aspecto.