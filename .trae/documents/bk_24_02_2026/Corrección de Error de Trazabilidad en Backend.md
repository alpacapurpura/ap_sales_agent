# Corrección Integral de Trazabilidad y Limpieza de Código

He auditado el código base en busca del error `NameError: name 'Repository' is not defined` y otras inconsistencias relacionadas.

## 🔍 Diagnóstico Final

El error está aislado en **`src/core/tracing.py`**.
- **Problema Crítico:** La función `wrapper_sync` (línea 153) intenta instanciar `Repository()` que no existe.
- **Problema Secundario:** El mismo archivo contiene una versión duplicada e incompleta de `wrapper_sync` (líneas 21-147) que es "código muerto" pero genera confusión y riesgo de mantenimiento.

El resto de archivos (`openai.py`, `gemini.py`, `admin.py`, `app.py`) usan correctamente `AuditRepository`, por lo que el sistema es estable fuera de este punto de fallo.

## 🛠️ Plan de Ejecución

1.  **Refactorizar `src/core/tracing.py`**:
    *   Eliminar el bloque de código muerto (la primera definición de `wrapper_sync`).
    *   Corregir la instanciación del repositorio en la función activa:
        ```python
        # Antes
        repo = Repository()
        
        # Después
        db = SessionLocal()
        repo = AuditRepository(db)
        ```
    *   Asegurar el cierre correcto de la sesión en el bloque `finally`.

2.  **Verificación**:
    *   El reinicio automático de Docker aplicará los cambios.
    *   El sistema debería dejar de enviar el mensaje de error "Internal Server Error" en Telegram.
