"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2, Copy, Check } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { bookingLinksApi } from "@/lib/api/booking-links";
import { leadsApi } from "@/lib/api/leads";

import type { Lead } from "@/lib/api/leads";

interface GenerateLinkModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  eventSlug: string;
}

/**
 *
 */
export function GenerateLinkModal({ open, onOpenChange, eventSlug }: GenerateLinkModalProps) {
  const { getToken } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [expiration, setExpiration] = useState("7");
  const [loading, setLoading] = useState(false);
  const [generatedUrl, setGeneratedUrl] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (val: string) => {
    setSearchQuery(val);
    if (val.length < 2) {
      setLeads([]);
      return;
    }

    setSearching(true);
    try {
      const token = await getToken();
      if (!token) return;
      const results = await leadsApi.search(val, token);
      setLeads(results);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedLead) return;
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const res = await bookingLinksApi.create(
        {
          lead_id: selectedLead.id,
          event_slug: eventSlug,
          expiration_days: parseInt(expiration),
        },
        token,
      );

      const fullUrl = `${window.location.origin}${res.url}`;
      setGeneratedUrl(fullUrl);
      toast.success("Link generado correctamente");
    } catch (e) {
      toast.error("Error generando link");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (generatedUrl) {
      void navigator.clipboard.writeText(generatedUrl);
      toast.success("Copiado al portapapeles");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Generar Link Personalizado</DialogTitle>
          <DialogDescription>Crea un enlace único para un lead específico.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {!generatedUrl ? (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Buscar Lead</label>
                <Input
                  placeholder="Nombre o email..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                />
                {searching && <div className="text-xs text-muted-foreground">Buscando...</div>}

                {leads.length > 0 && !selectedLead && (
                  <div className="border rounded-md max-h-[200px] overflow-y-auto mt-2 bg-background">
                    {leads.map((lead) => (
                      <div
                        key={lead.id}
                        className="p-2 hover:bg-accent cursor-pointer text-sm"
                        onClick={() => {
                          setSelectedLead(lead);
                          setSearchQuery(lead.full_name || lead.email);
                          setLeads([]);
                        }}
                      >
                        <div className="font-medium">{lead.full_name}</div>
                        <div className="text-xs text-muted-foreground">{lead.email}</div>
                      </div>
                    ))}
                  </div>
                )}
                {selectedLead && (
                  <div className="flex items-center justify-between p-2 border rounded-md bg-accent/20">
                    <div>
                      <div className="font-medium">{selectedLead.full_name}</div>
                      <div className="text-xs text-muted-foreground">{selectedLead.email}</div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedLead(null);
                        setSearchQuery("");
                      }}
                    >
                      Cambiar
                    </Button>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Expiración</label>
                <Select value={expiration} onValueChange={setExpiration}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7">7 días</SelectItem>
                    <SelectItem value="14">14 días</SelectItem>
                    <SelectItem value="30">30 días</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                className="w-full"
                onClick={handleGenerate}
                disabled={!selectedLead || loading}
              >
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Generar Link
              </Button>
            </>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-muted rounded-md break-all text-sm font-mono">
                {generatedUrl}
              </div>
              <div className="flex gap-2">
                <Button className="flex-1" onClick={copyToClipboard}>
                  <Copy className="mr-2 h-4 w-4" /> Copiar Link
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setGeneratedUrl(null);
                    setSelectedLead(null);
                    setSearchQuery("");
                  }}
                >
                  Generar otro
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
