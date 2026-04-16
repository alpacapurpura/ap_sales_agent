"use client";

import { Zap } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "@/components/ui/detail-panel";

import { getChannelIcon, getChannelColor } from "../../../lib/channel-icons";

import type { ChannelMetric } from "../../../types/metrics";

interface NoDataSidebarPanelProps {
  isOpen: boolean;
  onClose: () => void;
  channel: ChannelMetric | null;
}

export function NoDataSidebarPanel({ isOpen, onClose, channel }: NoDataSidebarPanelProps) {
  if (!channel) return null;

  const Icon = getChannelIcon(channel.slug);
  const iconColor = getChannelColor(channel.slug);

  return (
    <DetailPanel open={isOpen} onClose={onClose} size="sm">
      <DetailPanelHeader>
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg"
            style={{ backgroundColor: `${iconColor}20` }}
          >
            {/* eslint-disable-next-line react-hooks/static-components */}
            <Icon className="w-4 h-4" style={{ color: iconColor }} aria-hidden="true" />
          </div>
          <DetailPanelTitle>{channel.name}</DetailPanelTitle>
        </div>
        <DetailPanelClose onClose={onClose} />
      </DetailPanelHeader>

      <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
        <div className="w-16 h-16 rounded-full bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center mb-4">
          <Zap className="w-8 h-8 text-amber-600 dark:text-amber-400" />
        </div>

        <h3 className="text-lg font-semibold text-foreground mb-2">
          Próximamente: triggers &amp; actions
        </h3>

        <p className="text-sm text-muted-foreground max-w-xs mb-6">
          Pronto podrás crear acciones automáticas para activar este canal y sacarle el máximo
          provecho a tu conexión.
        </p>

        <Button variant="outline" onClick={onClose}>
          Cerrar
        </Button>
      </div>
    </DetailPanel>
  );
}
