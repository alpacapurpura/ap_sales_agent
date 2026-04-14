"use client";

import React from "react";
import {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "@/components/ui/detail-panel";
import { Badge } from "@/components/ui/badge";
import { MarketingActionLink } from "../config/types";

interface ActionDetailsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  link: MarketingActionLink | null;
}

const ActionDetailsDrawer: React.FC<ActionDetailsDrawerProps> = ({ isOpen, onClose, link }) => {
  return (
    <DetailPanel open={isOpen} onClose={onClose}>
      <DetailPanelHeader className="flex flex-row items-start justify-between pr-6">
        <div className="space-y-1">
          <DetailPanelTitle>{link?.label || "Detalles de Acción"}</DetailPanelTitle>
          <p className="text-sm text-muted-foreground">
            Análisis detallado del flujo de la estrategia.
          </p>
        </div>
        <DetailPanelClose onClose={onClose} className="flex-shrink-0" />
      </DetailPanelHeader>

      {link && (
        <div className="mt-6 space-y-6 px-6">
          {/* Status & Channel */}
          <div className="flex flex-wrap gap-2">
            <Badge variant={link.status === "BOTTLENECK" ? "destructive" : "default"}>
              {link.status}
            </Badge>
            <Badge variant="outline">{link.channelType.replace("_", " ")}</Badge>
            <Badge variant="secondary">{link.financialNature}</Badge>
          </div>

          {/* Main Value */}
          <div className="space-y-1">
            <h4 className="text-sm font-medium leading-none text-muted-foreground">
              Volumen de Flujo
            </h4>
            <p className="text-3xl font-bold">{link.value.toLocaleString()}</p>
          </div>

          {/* Metadata */}
          {link.metadata && (
            <div className="space-y-4 border-t pt-4">
              <h4 className="text-sm font-medium">Métricas Clave</h4>
              <dl className="grid grid-cols-2 gap-4">
                {Object.entries(link.metadata).map(([key, value]) => (
                  <div key={key} className="space-y-1">
                    <dt className="text-xs text-muted-foreground capitalize">
                      {key.replace(/([A-Z])/g, " $1").trim()}
                    </dt>
                    <dd className="text-sm font-medium">
                      {typeof value === "number" &&
                      (key.toLowerCase().includes("cost") ||
                        key.toLowerCase().includes("revenue") ||
                        key.toLowerCase().includes("cpa"))
                        ? value.toLocaleString("es-MX", { style: "currency", currency: "MXN" })
                        : String(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          <div className="text-xs text-muted-foreground mt-8">
            <p>
              ID Origen: <span className="font-mono">{link.source}</span>
            </p>
            <p>
              ID Destino: <span className="font-mono">{link.target}</span>
            </p>
          </div>
        </div>
      )}
    </DetailPanel>
  );
};

export default ActionDetailsDrawer;
