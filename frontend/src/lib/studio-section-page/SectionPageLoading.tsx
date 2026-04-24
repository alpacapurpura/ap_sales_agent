import { Loader2 } from "lucide-react";

/**
 * Fallback neutro mientras `next/dynamic` resuelve el chunk de una
 * sección. Se mantiene minimal — el umbral de 200ms de `next/dynamic`
 * evita ruido visual cuando el chunk carga rápido.
 *
 * Lo usa `SectionDispatcher.tsx` de cada studio como `loading` prop de
 * cada `dynamic()` import.
 */
export function SectionPageLoading() {
  return (
    <div
      className="flex h-64 items-center justify-center"
      aria-label="Cargando sección"
    >
      <Loader2
        className="h-6 w-6 animate-spin text-muted-foreground"
        aria-hidden
      />
    </div>
  );
}
