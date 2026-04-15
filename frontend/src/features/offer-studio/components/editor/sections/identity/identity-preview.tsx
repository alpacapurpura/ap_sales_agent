import { Sparkles, Box, Tag, Edit2 } from "lucide-react";
import React from "react";
import { useFormContext } from "react-hook-form";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { cn } from "@/lib/utils";
import { getContrastColor } from "@/lib/utils/colors";

import { ARCHETYPE_METADATA } from "../../../../config/archetype-metadata";

import type { OfferArchetype } from "../../../../types";
import type { OfferFormValues } from "../../../../types/schema";

interface IdentityPreviewProps {
  data?: Partial<OfferFormValues>;
  onEdit?: () => void;
}

export const IdentityPreview = ({ data: propsData, onEdit }: IdentityPreviewProps) => {
  const form = useFormContext<OfferFormValues>();
  const data = propsData || (form ? form.watch() : null);
  const { settings } = useBrandSettings();

  // Handle missing data gracefully
  if (!data) {
    return (
      <div className="w-full flex items-center justify-center p-8 text-muted-foreground bg-muted/20 rounded-xl border border-dashed">
        <span className="text-sm">Sin datos de oferta</span>
      </div>
    );
  }

  const { public_name, archetype, delivery_model } = data;
  const visuals = settings?.visuals;

  const hasName = Boolean(public_name);

  // Get Metadata
  const archetypeMeta = archetype ? ARCHETYPE_METADATA[archetype as OfferArchetype] : null;
  const TypeIcon = archetypeMeta?.icon || Sparkles;

  // --- SAFE COLOR LOGIC ---
  const primaryColor = visuals?.primary_color || "#a855f7";
  const accentColor = visuals?.accent_color || "#f59e0b";
  const bgColor = visuals?.background_color || "#ffffff";
  const headingFont = visuals?.font_heading || "inherit";

  // Calculate text colors for accessibility using the utility
  const textPrimary = visuals?.text_primary_color || getContrastColor(bgColor);
  const textOnPrimary = getContrastColor(primaryColor);

  // Dynamic Styles
  const containerStyle = {
    backgroundColor: bgColor,
    borderColor: visuals ? `${primaryColor}20` : undefined,
    color: textPrimary,
  };

  const iconWrapperStyle = {
    // Glassmorphism effect
    background: `linear-gradient(135deg, ${primaryColor}10, ${accentColor}10)`,
    borderColor: `${primaryColor}30`,
    boxShadow: `0 8px 32px -4px ${primaryColor}20`,
  };

  const iconStyle = {
    color: primaryColor,
  };

  const titleStyle = {
    fontFamily: headingFont,
    color: textPrimary,
  };

  // Badge styles: ensure text is readable
  const badgeTypeStyle = {
    backgroundColor: `${primaryColor}15`,
    color: primaryColor,
    borderColor: `${primaryColor}30`,
  };

  const badgeDeliveryStyle = {
    color: textPrimary,
    borderColor: `${textPrimary}30`,
  };

  return (
    <div
      className={cn(
        "group relative w-full p-10 rounded-2xl border shadow-sm transition-all duration-500 overflow-hidden",
        !visuals && "bg-gradient-to-br from-purple-50 via-white to-amber-50/30 border-purple-100",
        "hover:shadow-lg hover:shadow-primary/5",
      )}
      style={containerStyle}
    >
      {/* Edit Trigger (Top Right) */}
      <div className="absolute top-4 right-4 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity z-10 flex gap-2">
        {onEdit && (
          <Button
            size="sm"
            variant="secondary"
            onClick={onEdit}
            className="shadow-sm bg-background/80 backdrop-blur-sm hover:bg-background border"
            style={{
              color: primaryColor,
              borderColor: `${primaryColor}20`,
            }}
          >
            <Edit2 className="h-3.5 w-3.5 mr-2" />
            Editar Identidad
          </Button>
        )}
      </div>

      <div className="flex flex-col items-center text-center gap-6 relative z-10">
        {/* Icon Wrapper */}
        <div
          className={cn(
            "relative flex items-center justify-center w-20 h-20 rounded-full mb-2 transition-transform duration-500 group-hover:scale-105",
            "border backdrop-blur-md",
            !visuals &&
              "bg-gradient-to-br from-purple-100 to-amber-50 border-purple-200/50 shadow-[0_0_20px_-5px_rgba(168,85,247,0.3)]",
          )}
          style={iconWrapperStyle}
        >
          <TypeIcon
            className={cn("w-9 h-9", !visuals && "text-purple-700")}
            strokeWidth={1.5}
            style={iconStyle}
          />

          {/* Inner Glow Ring */}
          <div className="absolute inset-0 rounded-full ring-1 ring-inset ring-white/40" />
        </div>

        {/* Title & Subtitle */}
        <div className="space-y-3 max-w-2xl">
          <h1
            className={cn(
              "text-4xl font-bold leading-tight",
              !hasName && "text-muted-foreground/40 italic font-sans",
            )}
            style={hasName ? titleStyle : undefined}
          >
            {hasName ? public_name : "Nombre de tu Oferta"}
          </h1>

          {archetypeMeta?.subtitle && (
            <p
              className="text-base max-w-lg mx-auto leading-relaxed opacity-80"
              style={{ color: textPrimary }}
            >
              {archetypeMeta.subtitle}
            </p>
          )}
        </div>

        {/* Badges */}
        <div className="flex flex-wrap justify-center gap-3 pt-2">
          {/* Type Badge */}
          <Badge
            variant="secondary"
            className={cn(
              "gap-1.5 py-1.5 px-4 text-sm font-medium transition-colors border",
              !visuals && "bg-purple-100 text-purple-800 border-purple-200",
            )}
            style={visuals ? badgeTypeStyle : undefined}
          >
            <Tag className="w-3.5 h-3.5 opacity-70" />
            {archetypeMeta?.label ||
              (archetype
                ? archetype.charAt(0).toUpperCase() + archetype.slice(1)
                : "Archetype no definido")}
          </Badge>

          {/* Delivery Badge */}
          <Badge
            variant="outline"
            className="gap-1.5 py-1.5 px-4 text-sm font-normal transition-colors bg-background/50 backdrop-blur-sm"
            style={visuals ? badgeDeliveryStyle : undefined}
          >
            <Box className="w-3.5 h-3.5 opacity-70" />
            {delivery_model || "Modelo no definido"}
          </Badge>
        </div>
      </div>

      {/* Decorative Background Elements (Subtle) */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden rounded-2xl pointer-events-none z-0">
        <div
          className={cn(
            "absolute top-[-20%] right-[-10%] w-[300px] h-[300px] rounded-full blur-[100px] opacity-10",
            !visuals && "bg-purple-200/20",
          )}
          style={{ backgroundColor: visuals ? primaryColor : undefined }}
        />
        <div
          className={cn(
            "absolute bottom-[-20%] left-[-10%] w-[300px] h-[300px] rounded-full blur-[100px] opacity-10",
            !visuals && "bg-amber-100/30",
          )}
          style={{ backgroundColor: visuals ? accentColor : undefined }}
        />
      </div>
    </div>
  );
};
