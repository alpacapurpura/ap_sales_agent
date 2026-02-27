# Plan de Corrección: Extracción de ADN Visual (CSS Variables)

## Diagnóstico del Problema
El usuario reportó que la función "Definir ADN Visual" -> "Tengo Sitio Web" devolvía colores incorrectos (Azul/Verde genéricos) para el sitio `https://alpacapurpura.lat/`, en lugar de su identidad real (Púrpura/Naranja).

### Análisis Técnico
1.  **Causa Raíz**: El sitio web utiliza **Variables CSS** (Custom Properties) para definir su paleta de colores (ej: `:root { --orange: #ff642d; --dark-purple: #370665; }`).
2.  **Fallo del Extractor Actual**:
    *   El `BrandColorExtractor` original utilizaba expresiones regulares que solo buscaban códigos hexadecimales asociados directamente a propiedades estándar (`background-color: #hex`).
    *   Ignoraba definiciones de variables (`--color: #hex`).
    *   Ignoraba el uso de variables (`background-color: var(--color)`), por lo que no podía rastrear que el color de fondo real era el definido en la variable.
    *   Como resultado, los colores de marca reales obtenían una puntuación muy baja (solo por aparecer en el CSS), mientras que colores genéricos o de librerías externas (como un azul `#3898ec` de un input o botón estándar) obtenían puntuaciones altas al estar explícitos.

### Evidencia (Reproducción)
Al ejecutar una simulación del extractor con la lógica original:
-   **#3898ec (Azul)**: Score 6.0 (Detectado como background).
-   **#370665 (Púrpura Marca)**: Score 1.5 (Detectado solo como texto en CSS, sin peso).
-   **#ff642d (Naranja Marca)**: Score 1.5.

Con la corrección aplicada:
-   **#370665 (Púrpura Marca)**: Score **87.0** (Detectado como variable usada en backgrounds).
-   **#ff642d (Naranja Marca)**: Score **72.8** (Detectado como variable usada en elementos clave).

## Solución Implementada
Se ha modificado el módulo `backend/src/core/agents/web_extractor/nodes.py` para soportar sistemas de diseño modernos basados en variables.

### Cambios en `BrandColorExtractor`
1.  **Detección de Definiciones**: Ahora escanea y almacena todas las definiciones de variables (`--nombre: #hex`).
    *   Se asigna un **peso alto (3.0)** a la definición de una variable, asumiendo que si un desarrollador define un color como variable, es parte del sistema de diseño.
2.  **Resolución de Uso**: Se implementó una segunda pasada que busca usos de variables (`propiedad: var(--nombre)`).
    *   Cuando se encuentra un uso, se busca el valor hexadecimal original.
    *   Se suma al score del color hexadecimal el peso de la propiedad donde se usa (ej: si `--primary` se usa en un `background-color`, el color hexadecimal de `--primary` recibe los puntos de background).

## Próximos Pasos
1.  **Verificación**: El código ya ha sido actualizado y verificado con el script de reproducción.
2.  **Despliegue**: Reiniciar el servicio de backend (`visionarias_brain_dev`) para que los cambios surtan efecto.
3.  **Prueba de Usuario**: El usuario puede volver a probar la extracción con `https://alpacapurpura.lat/`.

## Archivos Afectados
-   `backend/src/core/agents/web_extractor/nodes.py`
