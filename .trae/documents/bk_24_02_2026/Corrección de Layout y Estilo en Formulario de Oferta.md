# Solución de Superposición en Formulario de Oferta

El usuario reporta dos problemas visuales en el formulario de "Resumen de la Oferta" (`OfferSummaryForm`):
1.  **Superposición de Elementos**: Los campos "Nombre Interno" y "Precio" parecen estar colapsando o superponiéndose en pantallas medianas/pequeñas debido a la estructura de rejilla (`grid`).
2.  **Flechas de Input Number**: El input de tipo `number` muestra las flechas nativas (spinners) que tapan el contenido numérico.

## Plan de Acción

### 1. Reestructuración del Layout (Grid)
El código actual usa `grid-cols-1 md:grid-cols-2`. Para evitar problemas de espacio en el campo de precio (que ahora contiene dos elementos: selector + input), ajustaremos el layout para que sea más robusto.
*   Mantendremos `grid-cols-2` pero revisaremos el espaciado (`gap`).
*   Aseguraremos que el contenedor del precio (`flex gap-2`) tenga suficiente espacio y no fuerce un desbordamiento.

### 2. Eliminación de Spinners en Input Number
Los navegadores añaden flechas de incremento/decremento a los inputs numéricos que a menudo rompen el diseño. Usaremos una clase de utilidad en Tailwind o CSS global para ocultarlos.
*   Añadir clase `[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none` al input de precio.

### 3. Ajuste de Alineación
El usuario pidió mover un `div` debajo de otro, lo que sugiere que prefiere un diseño vertical (stacked) en lugar de columnas para estos dos campos específicos si el espacio es reducido.
*   Cambiaremos el layout de `grid-cols-1 md:grid-cols-2` a una estructura vertical (`space-y-4`) para "Nombre Interno" y "Precio", o ajustaremos el breakpoint para que colapsen antes si es necesario. Sin embargo, la solicitud explícita es "pon este div debajo de este otro", lo que implica quitar el grid de 2 columnas para estos elementos específicos.

## Cambios Propuestos en `frontend/src/components/offer-studio/offer-summary-form.tsx`

```tsx
// Antes
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  <div className="space-y-2">...Nombre...</div>
  <div className="space-y-2">...Precio...</div>
</div>

// Después (Layout Vertical como solicitado)
<div className="space-y-4">
  <div className="space-y-2">...Nombre...</div>
  <div className="space-y-2">...Precio...</div>
</div>
```

Además, aplicaremos las clases para ocultar las flechas del input numérico.
