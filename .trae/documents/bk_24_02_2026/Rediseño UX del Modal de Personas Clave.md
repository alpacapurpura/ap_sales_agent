# Mejora UX/UI del Modal "Editar Persona"

El objetivo es rediseñar el modal de edición de "Personas Clave" para solucionar los problemas de espacio, alineación y usabilidad reportados. Se aplicará un diseño más vertical, espacioso y organizado.

## Estrategia de Diseño (UX/UI)

1. **Layout Vertical ("Label Top")**: Cambiar de una cuadrícula forzada (`grid-cols-4`) con etiquetas a la izquierda, a un diseño donde las etiquetas estén encima de los inputs. Esto maximiza el ancho útil para los campos de texto y mejora la legibilidad en modales.
2. **Ampliación del Modal**: Aumentar el ancho máximo del modal (`max-w-[500px]` -> `max-w-[700px]`) para evitar la sensación de "apretado".
3. **Agrupación Lógica**:

   * **Identidad**: Nombre y Rol en la misma fila (2 columnas).

   * **Perfil**: Género y Estilo en la misma fila (2 columnas).

   * **Narrativa**: Bio (Hook) ocupando el ancho completo.

   * **Configuración**: Switch de "Voz Principal" destacado.

   * **Contacto**: Grid de 2 columnas para redes sociales, con iconos visuales (si es posible con las librerías actuales) o etiquetas claras.
4. **Scroll Inteligente**: Asegurar que el contenido del modal tenga scroll interno (`max-h-[80vh] overflow-y-auto`) para pantallas pequeñas.

## Cambios en Código (`authority-squad-form.tsx`)

1. **Modificar** **`DialogContent`**:

   * Clase `sm:max-w-[500px]` -> `sm:max-w-[700px]`.

   * Agregar `max-h-[85vh] overflow-y-auto` al contenedor del formulario o al `DialogContent`.
2. **Reestructurar el Formulario (Team Modal)**:

   * Eliminar los `grid grid-cols-4 items-center gap-4`.

   * Usar contenedores `flex flex-col gap-2` para cada campo (Label + Input).

   * Usar `grid grid-cols-2 gap-4` para agrupar campos pares (Nombre/Rol, Redes).
3. **Sección de Redes**:

   * Grid de 2 columnas.

   * Etiquetas más limpias.

## Verificación

* Visual: El modal debe verse espacioso, con textos legibles y sin cortes.

* Funcional: Todos los campos deben seguir funcionando igual (el binding de estado no cambia, solo la presentación).

