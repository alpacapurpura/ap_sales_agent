"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, MoreHorizontal, Briefcase, Users, Loader2 } from "lucide-react";
import { Offer, offerApi } from "@/lib/api/offer";

export function OfferDashboard() {
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newOfferName, setNewOfferName] = useState("");
  const router = useRouter();

  useEffect(() => {
    setLoading(true);
    offerApi.listOffers()
      .then((data) => {
        setOffers(data);
        setError(null);
      })
      .catch((err) => {
        console.error("Dashboard Error:", err);
        setError("No se pudieron cargar las ofertas. Verifica que el backend esté corriendo.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleCreateOffer = async () => {
    if (!newOfferName.trim()) return;
    
    setCreating(true);
    try {
      const newOffer = await offerApi.createOffer(newOfferName);
      if (newOffer.id) {
        setIsDialogOpen(false);
        router.push(`/offer-studio/offer/${newOffer.id}`);
      }
    } catch (err) {
      console.error("Error creating offer:", err);
      setCreating(false);
    }
  };

  const openCreateDialog = () => {
    setNewOfferName("");
    setIsDialogOpen(true);
  };

  if (loading) {
    return <div className="flex justify-center p-8"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-red-500 space-y-4">
        <p className="text-lg font-medium">{error}</p>
        <Button variant="outline" onClick={() => window.location.reload()}>Reintentar</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Mis Ofertas</h2>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={openCreateDialog}>
              <Plus className="mr-2 h-4 w-4" /> Nueva Oferta
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Crear Nueva Oferta</DialogTitle>
              <DialogDescription>
                Comienza definiendo el nombre de tu oferta. Podrás configurar el resto de detalles (precio, promesa, avatar) en el siguiente paso.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nombre de la Oferta</Label>
                <Input 
                  id="name" 
                  placeholder="Ej: High Ticket Mentorship Q1" 
                  value={newOfferName}
                  onChange={(e) => setNewOfferName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreateOffer()}
                  autoFocus
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDialogOpen(false)} disabled={creating}>
                Cancelar
              </Button>
              <Button onClick={handleCreateOffer} disabled={creating || !newOfferName.trim()}>
                {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                {creating ? "Creando..." : "Crear Oferta"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">

        {/* Offer Cards */}
        {offers.map((offer) => (
          <Card key={offer.id} className="group relative hover:border-primary transition-colors">
            <CardHeader>
              <div className="flex justify-between items-start">
                 <CardTitle className="text-xl">{offer.name}</CardTitle>
                 <Button variant="ghost" size="icon" className="h-8 w-8">
                   <MoreHorizontal className="h-4 w-4" />
                 </Button>
              </div>
              <CardDescription>
                 {offer.status === "Active" ? <span className="text-green-500 font-medium">Activa</span> : <span className="text-muted-foreground">Borrador</span>}
                 {' • '}${offer.price}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground flex items-center gap-2">
                 <Users className="h-4 w-4" />
                 Avatar: <span className="font-medium text-foreground">{offer.avatar || "Global"}</span>
              </div>
            </CardContent>
            <CardFooter>
               <Link href={`/offer-studio/offer/${offer.id}`} className="w-full">
                 <Button className="w-full" variant="secondary">
                   <Briefcase className="mr-2 h-4 w-4" /> Gestionar
                 </Button>
               </Link>
            </CardFooter>
          </Card>
        ))}
        
        {offers.length === 0 && (
            <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-lg text-muted-foreground col-span-full md:col-span-1 lg:col-span-2">
                <p>No tienes ofertas creadas aún.</p>
                <Button variant="link" onClick={openCreateDialog}>Crear mi primera oferta</Button>
            </div>
        )}
      </div>
    </div>
  );
}
