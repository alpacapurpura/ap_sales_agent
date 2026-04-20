"use client";

interface CostLinkProps {
  href?: string;
}

/**
 *
 */
export function CostLink({ href = "/growth/settings/costs" }: CostLinkProps) {
  return (
    <div className="flex flex-col">
      <span className="text-sm text-muted-foreground">---</span>
      <a href={href} className="text-[10px] text-primary hover:underline cursor-pointer">
        Configurar costo
      </a>
    </div>
  );
}
