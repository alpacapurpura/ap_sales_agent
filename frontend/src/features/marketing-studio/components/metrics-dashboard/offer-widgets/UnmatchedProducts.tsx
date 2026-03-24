'use client';

import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { AlertTriangle, Link2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { metricsApi, type UnmatchedProduct } from '../../../api/metrics-api';
import { offerApi } from '@/features/offer-studio/api';
import type { Offer } from '@/features/offer-studio/types';

interface UnmatchedProductsProps {
  source?: string;
}

export function UnmatchedProducts({ source = 'shopify' }: UnmatchedProductsProps) {
  const { getToken } = useAuth();
  const [products, setProducts] = useState<UnmatchedProduct[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [selectedOffers, setSelectedOffers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    setLoading(true);
    try {
      const [unmatchedRes, offersRes] = await Promise.all([
        metricsApi.getUnmatchedProducts(token, source),
        offerApi.listOffers(token),
      ]);
      setProducts(unmatchedRes);
      setOffers(offersRes);
    } catch {
      // Silently fail — not critical
    } finally {
      setLoading(false);
    }
  }, [getToken, source]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const handleAssociate = async (product: UnmatchedProduct) => {
    const offerId = selectedOffers[product.external_id];
    if (!offerId) return;

    const token = await getToken();
    if (!token) return;

    setSaving(product.external_id);
    try {
      await metricsApi.createProductMapping(token, {
        offer_id: offerId,
        source,
        external_id: product.external_id,
        external_name: product.external_name ?? undefined,
      });
      setProducts((prev) => prev.filter((p) => p.external_id !== product.external_id));
    } catch {
      // Could add toast here
    } finally {
      setSaving(null);
    }
  };

  if (loading) return null;
  if (products.length === 0) return null;

  return (
    <div className="mt-8 rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50/50 dark:bg-amber-950/20 p-5">
      <h3 className="text-sm font-semibold flex items-center gap-2 text-amber-900 dark:text-amber-200 mb-3">
        <AlertTriangle className="w-4 h-4 text-amber-500" />
        Productos sin Oferta Asociada ({products.length})
      </h3>
      <p className="text-xs text-muted-foreground mb-4">
        Estos productos de Shopify aparecen en tus ventas pero no estan asociados a ninguna oferta del Offer Ladder.
        Asocialos para ver metricas desglosadas por oferta.
      </p>
      <div className="space-y-3">
        {products.map((product) => (
          <div
            key={product.external_id}
            className="flex flex-col sm:flex-row items-start sm:items-center gap-3 bg-background rounded-lg border border-border p-3"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {product.external_name || `Producto #${product.external_id}`}
              </p>
              <p className="text-xs text-muted-foreground">
                {product.event_count} transaccion{product.event_count !== 1 ? 'es' : ''}
                {product.total_price != null && product.currency && (
                  <> &middot; {new Intl.NumberFormat('es-MX', { style: 'currency', currency: product.currency, minimumFractionDigits: 0 }).format(product.total_price)}</>
                )}
              </p>
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Select
                value={selectedOffers[product.external_id] || ''}
                onValueChange={(val) =>
                  setSelectedOffers((prev) => ({ ...prev, [product.external_id]: val }))
                }
              >
                <SelectTrigger className="w-full sm:w-[200px] h-8 text-xs">
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
              <Button
                size="sm"
                variant="outline"
                className="h-8 text-xs shrink-0"
                disabled={!selectedOffers[product.external_id] || saving === product.external_id}
                onClick={() => void handleAssociate(product)}
              >
                {saving === product.external_id ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <>
                    <Link2 className="w-3 h-3 mr-1" /> Asociar
                  </>
                )}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
