Voy a solucionar el problema de "pantalla en blanco" y los errores de referencia en el frontend.

### Diagnóstico
1.  **ReferenceError: ModeToggle is not defined**: Los logs del contenedor muestran claramente que `app-sidebar.tsx` está intentando usar `<ModeToggle />` en la línea 132, pero el componente no está definido en el ámbito de la función `NavContent`.
    *   **Causa Raíz**: `NavContent` es un componente definido *dentro* de `AppSidebar`. Aunque `ModeToggle` se importa en el archivo, su uso dentro de la sub-función parece estar causando problemas de alcance o renderizado en el entorno de servidor/cliente de Next.js, o más probablemente, el error de compilación anterior dejó el estado inconsistente. Sin embargo, mirando el código, `ModeToggle` *está* importado. El error "not defined" en tiempo de ejecución suele indicar que la importación falló silenciosamente (quizás por el problema anterior de `node_modules`) o hay una referencia circular.
    *   Pero más crítico: El error `ReferenceError` en el log es explícito.
2.  **Hydration Mismatch**: Al usar `next-themes`, es obligatorio agregar `suppressHydrationWarning` en la etiqueta `<html>`. Revisé `layout.tsx` y **no** tiene este atributo, lo que causará errores de hidratación y parpadeos, aunque no necesariamente la pantalla blanca completa (eso es por el error de referencia).

### Plan de Acción
1.  **Corregir `layout.tsx`**: Agregaré `suppressHydrationWarning` a la etiqueta `<html>` para cumplir con los requisitos de `next-themes`.
2.  **Refactorizar `app-sidebar.tsx`**:
    *   Extraeré `NavContent` fuera del componente principal `AppSidebar` o me aseguraré de que `ModeToggle` se pase correctamente.
    *   Para ir a lo seguro y seguir las "best practices" (Single Responsibility Principle), moveré `NavContent` a su propio archivo o simplificaré la estructura para evitar definiciones de componentes anidados que a veces confunden al compilador de Next.js/React si no se manejan con cuidado.
    *   *Corrección Rápida*: Simplemente verificaré que la importación esté siendo reconocida. Dado que el log dice "ModeToggle is not defined" en la línea 132, y veo que está importado arriba, es muy probable que el build anterior fallido haya dejado "basura". Sin embargo, voy a asegurar el código.
3.  **Reiniciar Contenedor**: Haré un rebuild limpio para asegurar que todas las referencias se resuelvan.

**Pasos Técnicos:**
1.  Editar `frontend/src/app/layout.tsx` -> agregar `suppressHydrationWarning`.
2.  Editar `frontend/src/components/layout/app-sidebar.tsx` -> Asegurar que `ModeToggle` se usa correctamente. El código actual define `NavContent` *dentro* de `AppSidebar`. Esto es un antipatrón en React porque `NavContent` se re-crea en cada render. Lo extraeré o lo convertiré en una función de renderizado simple.
3.  Reiniciar contenedor.
