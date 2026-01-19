"use client";

import { useEffect, useState } from "react";
import { Offer, offerApi } from "@/lib/api/offer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Save, AlertCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import Link from "next/link";

export function OfferSummaryForm({ offerId }: { offerId: string }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [offer, setOffer] = useState<Offer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    offerApi.getOffer(offerId)
      .then((data) => {
        setOffer(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("No se pudo cargar la oferta. Es posible que no exista o haya sido eliminada.");
        setLoading(false);
      });
  }, [offerId]);

  const handleSave = async () => {
    if (!offer) return;
    setSaving(true);
    setMessage(null);
    try {
      await offerApi.saveOffer(offerId, offer);
      setMessage("Guardado correctamente");
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      console.error(err);
      setMessage("Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;
  }

  if (error || !offer) {
    return (
        <div className="p-8 max-w-2xl mx-auto">
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error || "Error desconocido cargando la oferta."}</AlertDescription>
            </Alert>
            <div className="mt-4 text-center">
                <Link href="/offer-studio">
                    <Button variant="outline">Volver al Dashboard</Button>
                </Link>
            </div>
        </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Resumen de la Oferta</h1>
        <div className="flex items-center gap-4">
            {message && (
                <span className={`text-sm ${message.includes("Error") ? "text-red-500" : "text-green-600"} transition-all`}>
                    {message}
                </span>
            )}
            <Button onClick={handleSave} disabled={saving}>
            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            {saving ? "Guardando..." : "Guardar Cambios"}
            </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Detalles Principales</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Nombre Interno</Label>
              <Input 
                value={offer.name} 
                onChange={(e) => setOffer({ ...offer, name: e.target.value })} 
              />
            </div>
            <div className="space-y-2">
              <Label>Precio (USD)</Label>
              <Input 
                type="number" 
                value={offer.price} 
                onChange={(e) => setOffer({ ...offer, price: parseFloat(e.target.value) || 0 })} 
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Promesa de Transformación (Big Promise)</Label>
            <Textarea 
              className="min-h-[100px]" 
              value={offer.promise}
              onChange={(e) => setOffer({ ...offer, promise: e.target.value })}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
