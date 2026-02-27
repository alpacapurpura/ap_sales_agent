
# Rediseño del Chat Timeline (Vertical + Trazas Horizontales)

Entiendo perfectamente tu requerimiento. La visualización actual es "todo horizontal", pero lo correcto y más intuitivo (UX) es mantener el **flujo de conversación vertical** (como WhatsApp o ChatGPT), y encapsular los **procesos internos (nodos)** en bloques horizontales intermedios.

## Nueva Propuesta de Diseño (Best Practices)

1.  **Flujo Principal Vertical:** Los mensajes del usuario y del bot volverán a apilarse de arriba a abajo.
2.  **Bloques de "Pensamiento" (Trazas):** Cuando el sistema ejecute pasos internos (nodos), estos se agruparán en un **contenedor horizontal deslizable** situado entre los mensajes.
3.  **Encapsulamiento Visual:**
    *   Los nodos se mostrarán dentro de una tarjeta sutil llamada "System Process" o "Traza de Ejecución".
    *   Usaremos un scroll horizontal (`ScrollArea`) para que si hay muchos nodos, no rompan el ancho de la pantalla.
    *   Añadiremos flechas (`->`) entre nodos para indicar la secuencia lógica.

## Implementación Técnica

1.  **Agrupación de Eventos:** Refactorizaré el componente para pre-procesar el array `timeline`. En lugar de renderizar ítem por ítem, agruparé secuencias de eventos tipo `trace` en un solo objeto `TraceGroup`.
2.  **Renderizado Condicional:**
    *   Si el grupo es `message`: Renderiza la burbuja de chat vertical (izquierda/derecha).
    *   Si el grupo es `trace_group`: Renderiza un contenedor horizontal con todos los nodos dentro.
3.  **Estilos:** Ajustaré CSS para que los mensajes ocupen el ancho completo disponible (con sus márgenes) y los bloques de traza sean compactos.

Esto te dará lo mejor de ambos mundos: legibilidad de chat y detalle técnico sin invadir el espacio vertical.
