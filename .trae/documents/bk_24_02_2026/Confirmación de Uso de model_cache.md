# Plan de Configuración de Pruebas y Reglas

He preparado el entorno y las reglas para asegurar la calidad del código mediante pruebas unitarias.

## 1. Nueva Regla: `unit-test-rules.md`
Crearé el archivo en `.trae/rules/` con las siguientes directrices (< 1000 caracteres):
*   **Centralización**: Todos los tests irán en la carpeta `scripts/`.
*   **Estructura**:
    *   `scripts/tests/unit/`: Para pruebas formales y permanentes.
    *   `scripts/temp/`: Para scripts "sucios" de validación rápida.
*   **Framework**: Estandarización sobre `pytest`.

## 2. Actualización de Dependencias
He detectado que faltan librerías de testing en `requirements.txt`.
*   **Acción**: Agregar `pytest` y `pytest-asyncio` para soportar pruebas asíncronas (necesarias por `FastAPI` y `LangGraph`).

## 3. Estructura de Directorios
Crearé la jerarquía necesaria para cumplir la regla:
*   `scripts/tests/unit` (Para tests unitarios)
*   `scripts/tests/integration` (Para el futuro)
*   `scripts/temp` (Ya creado, confirmaré permisos)

## 4. Limpieza (Solicitud Anterior)
*   Eliminar la carpeta `docs/venv` que no se utiliza.
