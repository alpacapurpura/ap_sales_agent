import React, { forwardRef } from 'react';
import { cn } from '@/shared/lib/utils';
// Opcional: importar iconos
// import { ChevronRight } from 'lucide-react';

/**
 * Interfaces separadas y exportadas por si otras partes 
 * de la UI necesitan componer este componente.
 */
export interface ComponentNameProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Descripción de la prop principal. Usa JSDoc para que el
   * linter del equipo lo detecte.
   */
  variant?: 'default' | 'outline' | 'ghost';
  /**
   * Indicador de estado de carga
   */
  isLoading?: boolean;
}

/**
 * Nombre del Componente (ComponentName)
 * * Este componente asume la arquitectura FSD. 
 * Si maneja estado interno, asegúrate de marcar el archivo con "use client" en la primera línea.
 * Envuelve en forwardRef para permitir la composición de componentes en Radix/Shadcn UI.
 */
export const ComponentName = forwardRef<HTMLDivElement, ComponentNameProps>(
  (
    { 
      className, 
      variant = 'default', 
      isLoading = false,
      children,
      ...props 
    }, 
    ref
  ) => {
    
    // Lógica de derivación de estado aquí (preferir sobre useEffect)

    return (
      <div
        ref={ref}
        className={cn(
          "relative flex items-center justify-center rounded-md p-4 transition-colors",
          {
            "bg-primary text-primary-foreground hover:bg-primary/90": variant === 'default',
            "border border-input bg-background hover:bg-accent hover:text-accent-foreground": variant === 'outline',
            "hover:bg-accent hover:text-accent-foreground": variant === 'ghost',
            "opacity-50 pointer-events-none cursor-not-allowed": isLoading,
          },
          className
        )}
        aria-busy={isLoading}
        {...props}
      >
        {/* Renderizado de iconos o estados */}
        {isLoading && (
          <span className="absolute left-2 animate-spin">
             {/* <Loader2 className="w-4 h-4" /> */}
          </span>
        )}
        
        {/* Contenido principal */}
        {children}
      </div>
    );
  }
);

// Necesario al usar forwardRef para mantener los DevTools limpios
ComponentName.displayName = 'ComponentName';