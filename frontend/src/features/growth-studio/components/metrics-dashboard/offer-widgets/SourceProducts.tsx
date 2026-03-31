'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@clerk/nextjs';
import { AlertTriangle, CheckCircle2, Package } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { metricsApi, type SourceProduct } from '../../../api/metrics-api';
import { offerApi } from '@/features/offer-studio/api';
import type { Offer } from '@/features/offer-studio/types';
import { AssociationDialog } from './AssociationDialog';

const SOURCE_LABELS: Record<string, string> = {
  shopify: 'Shopify',
  woocommerce: 'WooCommerce',
  stripe: 'Stripe',
};

interface SourceProductsProps {
  source?: string;
}

export function SourceProducts({ source = 'shopify' }: SourceProductsProps) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const [dialogProduct, setDialogProduct] = useState<SourceProduct | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const { data: products = [], isLoading: loadingProducts } = useQuery<SourceProduct[]>({
    queryKey: ['source-products', source],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return metricsApi.getSourceProducts(token, source);
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: offers = [] } = useQuery<Offer[]>({
    queryKey: ['offers'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return offerApi.listOffers(token);
    },
    staleTime: 5 * 60 * 1000,
  });

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleAssociationSuccess = (salesCreated: number) => {
    const msg = salesCreated > 0
      ? `Producto asociado. ${salesCreated} venta${salesCreated !== 1 ? 's' : ''} retroactiva${salesCreated !== 1 ? 's' : ''} creada${salesCreated !== 1 ? 's' : ''}.`
      : 'Producto asociado correctamente.';
    setToast(msg);
    void queryClient.invalidateQueries({ queryKey: ['source-products', source] });
    void queryClient.invalidateQueries({ queryKey: ['sales-detail'] });
  };

  const unmappedProducts = products.filter((p) => !p.is_mapped);

  if (loadingProducts) return null;
  if (unmappedProducts.length === 0) return null;

  const sourceLabel = SOURCE_LABELS[source] || source;

  const formatCurrency = (value: number, currency: string | null) =>
    new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: currency || 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);

  return (
    <>
      <div className="bg-card rounded-xl p-6 border border-border">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold flex items-center gap-2 text-foreground">
            <Package className="w-4 h-4 text-emerald-600 dark:text-emerald-500" />
            Productos sin Asociar
            <span className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-xs font-medium">
              {unmappedProducts.length}
            </span>
          </h3>
        </div>

        {/* Toast */}
        {toast && (
          <div className="mb-4 flex items-center gap-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 px-3 py-2 text-xs text-emerald-800 dark:text-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
            {toast}
          </div>
        )}

        {/* Product list */}
        <div className="space-y-2">
          {unmappedProducts.map((product) => (
            <div
              key={product.external_id}
              className="flex items-center gap-3 bg-background rounded-lg border border-border p-3"
            >
              {/* Name */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {product.external_name || `Producto #${product.external_id}`}
                </p>
              </div>

              {/* Metrics */}
              <div className="text-right shrink-0">
                <p className="text-sm font-semibold">
                  {formatCurrency(product.total_price, product.currency)}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {product.event_count} transaccion{product.event_count !== 1 ? 'es' : ''}
                </p>
              </div>

              {/* Associate button */}
              <div className="shrink-0 ml-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800 hover:bg-amber-50 dark:hover:bg-amber-950/30"
                  onClick={() => setDialogProduct(product)}
                >
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  Asociar
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <AssociationDialog
        product={dialogProduct}
        offers={offers}
        source={source}
        open={dialogProduct !== null}
        onOpenChange={(open) => { if (!open) setDialogProduct(null); }}
        onSuccess={handleAssociationSuccess}
      />
    </>
  );
}
