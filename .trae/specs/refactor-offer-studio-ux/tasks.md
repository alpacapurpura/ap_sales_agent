# Tasks

- [ ] Task 1: Reestructurar el Layout Principal (`OfferStudioLayout.tsx`)
  - [ ] SubTask 1.1: Mover el Header (Título y Acciones) fuera del contenedor principal para que ocupe el ancho completo y sea `sticky top-0`.
  - [ ] SubTask 1.2: Reorganizar el contenedor flex para que el Sidebar y el Contenido Principal estén debajo del Header.

- [ ] Task 2: Mejorar la Barra Lateral (`OfferNavRail.tsx`)
  - [ ] SubTask 2.1: Implementar funcionalidad de colapsar/expandir (usando estado local o contexto).
  - [ ] SubTask 2.2: Ajustar estilos para que sea `sticky` y ocupe la altura restante de la pantalla (`calc(100vh - headerHeight)`).
  - [ ] SubTask 2.3: Cambiar el comportamiento de los enlaces para que realicen scroll al `id` de la sección en lugar de cambiar de modo/ruta.

- [ ] Task 3: Implementar Estilo "Editorial" en Secciones
  - [ ] SubTask 3.1: Crear un componente envoltorio (`OfferSectionWrapper`) que maneje los estados "Vacío" y "Resumen" similar a Brand Studio.
  - [ ] SubTask 3.2: Refactorizar el renderizado de secciones en `OfferStudioLayout` para usar este envoltorio y eliminar las `Card` actuales.
  - [ ] SubTask 3.3: Implementar el estado "Vacío" con diseño atractivo (Icono, Título, Descripción, Botón "Comenzar").
  - [ ] SubTask 3.4: Conectar el botón de acción (y el de edición en estado lleno) para abrir el `Sheet` de edición existente.

- [ ] Task 4: Ajustes Visuales Finales
  - [ ] SubTask 4.1: Verificar espaciados, tipografías y sombras para igualar la estética de Brand Studio.
  - [ ] SubTask 4.2: Asegurar que el `OfferEditSheetManager` funcione correctamente con los nuevos triggers.
