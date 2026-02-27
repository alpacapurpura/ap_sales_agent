# Plan de Revisión y Documentación de Entidades del Backend

Este plan tiene como objetivo analizar exhaustivamente el backend para identificar, clasificar y describir todas las entidades de negocio y persistencia del sistema Visionarias Brain.

## Pasos de Ejecución

1.  **Análisis Sistemático por Módulo**
    *   Revisaré cada módulo en `backend/src/modules/` (`iam`, `sales`, `communication`, `offer`, `marketing`, `brand`, `landing`, `gallery`, `integration`) y `shared`.
    *   Identificaré todas las clases que hereden de `Base` (SQLAlchemy) y `BaseModel` (Pydantic).

2.  **Clasificación de Entidades**
    *   **Entidades de Dominio (Pydantic)**: Objetos de negocio utilizados en la lógica, validación y transferencia de datos (DTOs).
    *   **Entidades de Persistencia (SQLAlchemy)**: Modelos que representan tablas en la base de datos y sus relaciones.

3.  **Extracción de Detalles**
    *   Para cada entidad, documentaré:
        *   **Nombre**: Nombre de la clase.
        *   **Tipo**: Dominio o Base de Datos.
        *   **Ubicación**: Módulo y archivo.
        *   **Descripción**: Propósito y responsabilidad dentro del sistema.

4.  **Generación del Reporte Final**
    *   Compilaré toda la información en un documento estructurado (`entidades_backend.md`) que servirá como inventario completo de los activos de datos del negocio.
    *   El reporte estará organizado por módulo funcional para facilitar su lectura y comprensión.

## Entregable
*   Un archivo Markdown con el listado completo y detallado de todas las entidades del sistema.
