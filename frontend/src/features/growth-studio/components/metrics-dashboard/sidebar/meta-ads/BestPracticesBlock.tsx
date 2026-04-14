import { Lightbulb } from "lucide-react";

/**
 * Educational block explaining how Meta campaigns should be structured.
 * Used inside the Onboarding modal and the Offer Assignment drawer.
 *
 * Static content, no props — safe as a Server Component.
 */
export function BestPracticesBlock() {
  return (
    <div className="rounded-lg border bg-blue-500/5 p-4">
      <div className="mb-2 flex items-center gap-2">
        <Lightbulb className="h-4 w-4 text-blue-500" aria-hidden="true" />
        <h3 className="text-sm font-semibold">Cómo organizar tus campañas en Meta</h3>
      </div>
      <p className="text-xs text-muted-foreground mb-3">
        Para que Nicolify pueda mostrarte métricas claras por producto, la mejor estructura es:
      </p>
      <ul className="space-y-2 text-xs">
        <li className="flex gap-2">
          <span className="text-emerald-500 shrink-0" aria-hidden="true">
            ✓
          </span>
          <span>
            <strong className="text-foreground">1 campaña por producto/servicio</strong> (offer) —
            más simple de gestionar y medir
          </span>
        </li>
        <li className="flex gap-2">
          <span className="text-emerald-500 shrink-0" aria-hidden="true">
            ✓
          </span>
          <span>
            <strong className="text-foreground">
              El objective de la campaña define qué métrica vas a ver
            </strong>
            :
            <ul className="mt-1 ml-4 space-y-0.5 text-muted-foreground">
              <li>• Ventas → ROAS real</li>
              <li>• Leads → formularios completados</li>
              <li>• Mensajes → conversaciones iniciadas</li>
              <li>• Tráfico → visitas a tu landing (no esperes ventas)</li>
            </ul>
          </span>
        </li>
        <li className="flex gap-2">
          <span className="text-emerald-500 shrink-0" aria-hidden="true">
            ✓
          </span>
          <span>
            <strong className="text-foreground">
              Dentro de cada campaña, 2-3 ad sets con audiencias distintas
            </strong>{" "}
            — Meta aprende más rápido
          </span>
        </li>
        <li className="flex gap-2">
          <span className="text-emerald-500 shrink-0" aria-hidden="true">
            ✓
          </span>
          <span>
            <strong className="text-foreground">3-6 anuncios por ad set</strong> — Meta rota y elige
            el mejor
          </span>
        </li>
      </ul>
      <p className="mt-3 text-[11px] italic text-muted-foreground">
        Si usás CBO (Campaign Budget Optimization), podés asociar ad sets individuales a offers
        distintas.
      </p>
    </div>
  );
}
