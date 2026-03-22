'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { CandidatoData } from '../../../types/metrics';

interface Props {
  candidatos: CandidatoData[];
  onPromote: (customerId: string) => void;
  isPromoting: boolean;
}

export function CandidatosBanner({ candidatos, onPromote, isPromoting }: Props) {
  const [confirmId, setConfirmId] = useState<string | null>(null);

  if (candidatos.length === 0) return null;

  const selectedCandidate = candidatos.find((c) => c.customerId === confirmId);

  return (
    <>
      <div className="rounded-lg border border-dashed border-purple-300 dark:border-purple-700 p-3 space-y-2">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm font-semibold">Candidatos a Evangelista</span>
            <Badge variant="secondary" className="ml-2">
              {candidatos.length} total
            </Badge>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          Clientes con NPS {'>'}= 9 sin codigo de referido
        </p>

        {/* Candidate rows */}
        <div className="space-y-1">
          {candidatos.map((c) => {
            const initial = c.fullName.charAt(0).toUpperCase();
            return (
              <div key={c.customerId} className="flex items-center justify-between py-1">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-purple-100 dark:bg-purple-950/30 text-purple-600 dark:text-purple-400 flex items-center justify-center text-[10px] font-semibold flex-shrink-0">
                    {initial}
                  </div>
                  <span className="text-sm">{c.fullName}</span>
                  <Badge
                    variant="secondary"
                    className="bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400 text-xs"
                  >
                    NPS {c.npsScore}
                  </Badge>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-purple-600 dark:text-purple-400 border-purple-300 dark:border-purple-700"
                  onClick={() => setConfirmId(c.customerId)}
                >
                  Promover
                </Button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={confirmId !== null} onOpenChange={(open) => { if (!open) setConfirmId(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Promover a Evangelista</DialogTitle>
            <DialogDescription>
              Se creara un codigo de referido unico para{' '}
              {selectedCandidate?.fullName ?? 'este cliente'}. Podras compartirlo con el para que
              recomiende tu negocio.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmId(null)}>
              Cancelar
            </Button>
            <Button
              disabled={isPromoting}
              onClick={() => {
                if (confirmId) {
                  onPromote(confirmId);
                  setConfirmId(null);
                }
              }}
            >
              {isPromoting ? 'Procesando...' : 'Confirmar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
