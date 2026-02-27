# Nueva Propuesta de Diseño para Botón "Gestionar"

Basado en el feedback, cambiaré el enfoque de "botón secundario que se oscurece" a un **"botón de contorno que se rellena"**. Este es un patrón de diseño muy efectivo para tarjetas, ya que mantiene la interfaz limpia visualmente (outline) pero ofrece un feedback de interacción fuerte y claro (solid fill) al pasar el cursor.

## Detalles del Cambio

1.  **Estado Normal**:
    *   Variante: `outline` (Borde sutil, fondo transparente).
    *   Borde: Color primario con opacidad reducida (`border-primary/20`) para que no compita visualmente con el contenido pero sea visible.
    *   Texto: Color del texto normal.

2.  **Estado Hover (Interacción)**:
    *   Fondo: Se rellena con el color primario de la marca (`hover:bg-primary`).
    *   Texto: Cambia a color de contraste sobre primario (`hover:text-primary-foreground`).
    *   Borde: Se vuelve sólido (`hover:border-primary`).
    *   Efecto adicional: Sombra suave para dar profundidad (`hover:shadow-sm`).

3.  **Transición**:
    *   Duración: 300ms para una sensación de fluidez y elegancia.

## Código Propuesto

Modificaré el archivo `frontend/src/components/offer-studio/offer-dashboard.tsx`:

```tsx
<Button 
   className="w-full cursor-pointer border-primary/20 hover:bg-primary hover:text-primary-foreground hover:border-primary transition-all duration-300" 
   variant="outline"
>
   <Briefcase className="mr-2 h-4 w-4" /> Gestionar
</Button>
```

Esta alternativa elimina la sensación "apagada" del botón gris (secondary) y le da un comportamiento más dinámico y moderno.
