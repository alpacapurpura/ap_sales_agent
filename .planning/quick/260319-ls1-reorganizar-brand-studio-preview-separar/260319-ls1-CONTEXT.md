# Quick Task 260319-ls1: Reorganizar Brand Studio preview - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Task Boundary

Separar "Voz y comunicación" y "Target & Buyer Personas" de Block I (El ADN de Marca) en secciones independientes con su propia fila y numeración. Actualizar preview, sidebar/índice y health check counter.

</domain>

<decisions>
## Implementation Decisions

### Renumeración de bloques
- **5 bloques**: I. ADN de Marca, II. Voz & Comunicación, III. Público, IV. Universo Visual, V. Validación Social + Operaciones sin número
- Los headers del preview y del sidebar deben reflejar la nueva numeración

### Health check
- **Agregar Voice y Avatars como secciones scored independientes** en `getBrandHealth()`
- El promedio pasa de 7 a 9 secciones
- Cada una necesita su propia función `validateVoice()` y `validateAvatars()` en `brand-validation.ts`
- El health % puede bajar si están vacíos — esto es esperado

### Campo "Idioma Principal"
- Ya existe como `identity.language` en el modelo de datos (backend + frontend)
- Actualmente vive en el formulario de Identity y se muestra en Voice preview
- Solo reubicación visual: moverlo al nuevo bloque II. Voz & Comunicación
- Layout: Idioma Principal (1/4 del ancho) + Tono de voz (3/4 del ancho) en grid

### Claude's Discretion
- Iconos apropiados para las nuevas secciones del sidebar
- Subtítulos para los nuevos bloques II y III

</decisions>

<specifics>
## Specific Ideas

- Block II "Voz & Comunicación": grid con `grid-cols-4` — Idioma Principal ocupa `col-span-1`, Tono de voz ocupa `col-span-3`
- Block III "Público": contiene Target & Buyer Persona (componente AvatarsSection existente)
- Sidebar nav items: agregar "Voz" bajo grupo II y "Público/Target" bajo grupo III
- Status dots del sidebar deben conectar con las nuevas funciones de validación

</specifics>
