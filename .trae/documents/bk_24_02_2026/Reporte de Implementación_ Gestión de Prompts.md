# Solución: Persistencia de Prompts y Corrección de "Base de Datos Vacía"

He encontrado la causa raíz del problema.

## Diagnóstico
El archivo `src/main.py` ejecuta `init_db()` cada vez que arranca el sistema. Esta función (`src/services/database.py`) tiene configurado **borrar y recrear todas las tablas** (comportamiento de desarrollo), pero actualmente **solo restaura los Productos, no los Prompts**.

Por eso, aunque ejecuté el script de migración, al reiniciarse o conectarse el servicio, la base de datos se limpió y los prompts se perdieron.

## Plan de Corrección Definitiva

1.  **Integrar Prompts en `init_db`**:
    *   Modificaré `src/services/database.py` para que, además de crear los productos, **cargue automáticamente los prompts iniciales** desde los archivos `.j2`.
    *   Esto asegurará que los prompts "base" siempre existan, incluso si la base de datos se reinicia.

2.  **Restaurar Datos Ahora**:
    *   Ejecutaré manualmente el script de sembrado (`seed_prompts.py`) una vez más para que aparezcan inmediatamente en tu panel sin necesidad de reiniciar nada.

3.  **Verificación**:
    *   Comprobaré que la tabla `prompt_versions` tenga registros.
    *   Confirmaré que los metadatos (nodo, descripción) se estén guardando correctamente.

## Resultado Esperado
Al recargar la página Admin, verás la lista de prompts con toda su información (Nodo, Objetivo, Variables) tal como solicitaste.
