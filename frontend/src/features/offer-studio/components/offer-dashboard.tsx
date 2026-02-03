"use client";

import { useState, useEffect } from "react";
import { Plus, Search, Filter, MoreHorizontal, Package, Briefcase, GraduationCap, Repeat, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@clerk/nextjs";
import { offerApi, Offer } from "@/lib/api/offer";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

export type OfferCategory = "products" | "services" | "programs" | "subscriptions";

const UI_CONFIG: Record<OfferCategory, {
  buttonLabel: string;
  dialogTitle: string;
  dialogDescription: string;
  inputLabel: string;
  inputPlaceholder: string;
  emptyState: string;
  searchPlaceholder: string;
  createActionLabel: string;
}> = {
  products: {
    buttonLabel: "Nuevo Producto",
    dialogTitle: "Crear Nuevo Producto",
    dialogDescription: "Define el nombre público de tu producto digital o físico (Ej. Ebook, Template).",
    inputLabel: "Nombre del Producto",
    inputPlaceholder: "Ej. Guía Definitiva de SEO 2026",
    emptyState: "No tienes productos creados.",
    searchPlaceholder: "Buscar productos...",
    createActionLabel: "Crear Producto",
  },
  services: {
    buttonLabel: "Nuevo Servicio",
    dialogTitle: "Crear Nuevo Servicio",
    dialogDescription: "Define el nombre de tu servicio High Ticket o paquete de consultoría.",
    inputLabel: "Nombre del Servicio",
    inputPlaceholder: "Ej. Consultoría de Procesos",
    emptyState: "No tienes servicios activos.",
    searchPlaceholder: "Buscar servicios...",
    createActionLabel: "Crear Servicio",
  },
  programs: {
    buttonLabel: "Nuevo Programa",
    dialogTitle: "Crear Nuevo Programa",
    dialogDescription: "Define el nombre de tu formación, curso o mentoría grupal.",
    inputLabel: "Nombre del Programa",
    inputPlaceholder: "Ej. Agency Mastermind Q1",
    emptyState: "No tienes programas educativos.",
    searchPlaceholder: "Buscar programas...",
    createActionLabel: "Crear Programa",
  },
  subscriptions: {
    buttonLabel: "Nueva Suscripción",
    dialogTitle: "Crear Nueva Suscripción",
    dialogDescription: "Define el nombre de tu membresía o comunidad recurrente.",
    inputLabel: "Nombre de la Membresía",
    inputPlaceholder: "Ej. Inner Circle VIP",
    emptyState: "No tienes suscripciones activas.",
    searchPlaceholder: "Buscar suscripciones...",
    createActionLabel: "Crear Suscripción",
  },
};

export function OfferDashboard({ filterTypes, category = "programs" }: { filterTypes?: string[], category?: OfferCategory }) {
  const { getToken } = useAuth();
  const router = useRouter();
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const ui = UI_CONFIG[category];
  
  // Create Dialog State
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newOfferName, setNewOfferName] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const fetchOffers = async () => {
        try {
            const token = await getToken();
            if (!token) return;
            
            const data = await offerApi.listOffers(token);
            
            // Client-side filtering
            const filteredData = filterTypes 
                ? data.filter(offer => offer.type && filterTypes.includes(offer.type))
                : data;
                
            setOffers(filteredData);
            setError(null);
        } catch (err) {
            console.error("Error fetching offers:", err);
            setError("No se pudieron cargar las ofertas. Intenta nuevamente.");
        } finally {
            setLoading(false);
        }
    };

    fetchOffers();
  }, [getToken, filterTypes]);

  const handleCreateOffer = async () => {
    if (!newOfferName.trim()) return;
    
    setCreating(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("No authenticated");
      
      // Determine default type based on current tab filter
      // If we are in "Products" tab (filterTypes=['DIGITAL_PRODUCT', ...]), default to DIGITAL_PRODUCT
      const defaultType = filterTypes && filterTypes.length > 0 ? filterTypes[0] : "HYBRID_MENTORSHIP";
      
      const newOffer = await offerApi.createOffer({
        name: newOfferName,
        type: defaultType,
        status: "DRAFT"
      }, token);
      
      if (newOffer.id && newOffer.id !== 'undefined') {
        setIsDialogOpen(false);
        router.push(`/offer-studio/offer/${newOffer.id}`);
      } else {
          throw new Error("Created offer has invalid ID");
      }
    } catch (err) {
      console.error("Error creating offer:", err);
      // Optional: Show toast
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return <div className="flex h-48 items-center justify-center"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>;
  }

  if (error) {
    return <div className="text-destructive text-center p-8">{error}</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="relative w-72">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder={ui.searchPlaceholder} className="pl-8" />
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              {ui.buttonLabel}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{ui.dialogTitle}</DialogTitle>
              <DialogDescription>
                {ui.dialogDescription}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="name" className="text-right">
                  {ui.inputLabel}
                </Label>
                <Input
                  id="name"
                  value={newOfferName}
                  onChange={(e) => setNewOfferName(e.target.value)}
                  className="col-span-3"
                  placeholder={ui.inputPlaceholder}
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleCreateOffer} disabled={creating}>
                {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                {ui.createActionLabel}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {offers.length === 0 ? (
            <div className="col-span-full text-center p-12 border-2 border-dashed rounded-lg text-muted-foreground">
                {ui.emptyState}
            </div>
        ) : (
            offers.map((offer) => (
            <Card key={offer.id} className="cursor-pointer hover:border-primary/50 transition-colors" onClick={() => router.push(`/offer-studio/offer/${offer.id}`)}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium line-clamp-1">
                    {offer.name}
                </CardTitle>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="h-8 w-8 p-0" onClick={(e) => e.stopPropagation()}>
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                    </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                    <DropdownMenuLabel>Acciones</DropdownMenuLabel>
                    <DropdownMenuItem onClick={(e) => { e.stopPropagation(); router.push(`/offer-studio/offer/${offer.id}`); }}>
                        Editar
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-destructive" onClick={(e) => e.stopPropagation()}>
                        Archivar
                    </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
                </CardHeader>
                <CardContent>
                <div className="text-2xl font-bold">
                    {offer.currency} {offer.price}
                </div>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                    {offer.promise || "Sin promesa definida"}
                </p>
                <div className="mt-4 flex items-center gap-2">
                    <span className={`text-[10px] px-2 py-1 rounded-full ${
                        offer.status === "Active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                    }`}>
                        {offer.status || "Draft"}
                    </span>
                    <span className="text-[10px] text-muted-foreground bg-secondary px-2 py-1 rounded-full">
                        {offer.type?.replace("_", " ")}
                    </span>
                </div>
                </CardContent>
            </Card>
            ))
        )}
      </div>
    </div>
  );
}
