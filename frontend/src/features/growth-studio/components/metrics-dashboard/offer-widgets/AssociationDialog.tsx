'use client';

import { useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { useParams } from 'next/navigation';
import { Link2, Loader2 } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { metricsApi, type SourceProduct } from '../../../api/metrics-api';
import type { Offer } from '@/features/offer-studio/types';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';

interface AssociationDialogProps {
  product: SourceProduct | null;
  offers: Offer[];
  source: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (salesCreated: number) => void;
}

export function AssociationDialog({ product, offers, source, open, onOpenChange, onSuccess }: AssociationDialogProps) {
  const { getToken } = useAuth();
  const params = useParams();
  const tenantId = params?.tenantId as string;
  const { currency: tenantCurrency } = useTenantLocale();
  const [selectedOfferId, setSelectedOfferId] = useState<string>('');
  const [saving, setSaving] = useState(false);

  const handleAssociate = async () => {
    if (!product || !selectedOfferId) return;
    const token = await getToken();
    if (!token) return;

    setSaving(true);
    try {
      const result = await metricsApi.createProductMapping(token, {
        offer_id: selectedOfferId,
        source,
        external_id: product.external_id,
        external_name: product.external_name ?? undefined,
      });
      setSelectedOfferId('');
      onOpenChange(false);
      onSuccess(result.sales_created);
    } catch {
      // Error handled silently — could add toast
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (value: number, currency: string | null) =>
    new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: currency || tenantCurrency,
      minimumFractionDigits: 0,
    }).format(value);

  if (!product) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Asociar Producto</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Product info */}
          <div className="bg-muted/50 rounded-lg p-3">
            <p className="text-sm font-medium">
              {product.external_name || `Producto #${product.external_id}`}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {formatCurrency(product.total_price, product.currency)}
              {' · '}
              {product.event_count} transaccion{product.event_count !== 1 ? 'es' : ''}
            </p>
          </div>

          {/* Offer selection or empty state */}
          {offers.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-sm text-muted-foreground mb-3">
                No hay ofertas configuradas. Crea tu primera oferta en Offer Studio.
              </p>
              <a
                href={`/${tenantId}/offer-studio`}
                className="text-sm font-medium text-amber-700 dark:text-amber-400 hover:underline"
              >
                Ir a Offer Studio &rarr;
              </a>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Oferta destino</label>
                <Select value={selectedOfferId} onValueChange={setSelectedOfferId}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar oferta..." />
                  </SelectTrigger>
                  <SelectContent>
                    {offers.map((offer) => (
                      <SelectItem key={String(offer.id)} value={String(offer.id)}>
                        {offer.public_name || offer.name || offer.internal_sku || `Oferta ${String(offer.id).slice(0, 8)}`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button
                className="w-full"
                disabled={!selectedOfferId || saving}
                onClick={() => void handleAssociate()}
              >
                {saving ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Link2 className="w-4 h-4 mr-2" />
                )}
                Asociar
              </Button>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
