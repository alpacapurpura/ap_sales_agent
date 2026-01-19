import { OfferDashboard } from "@/components/offer-studio/offer-dashboard";

export default function OfferStudioPage() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Ecosistema de Ofertas</h1>
        <p className="text-muted-foreground">
          Gestiona tus productos y personaliza la IA para cada nicho.
        </p>
      </div>
      <OfferDashboard />
    </div>
  );
}
