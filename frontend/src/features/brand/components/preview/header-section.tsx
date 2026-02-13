import { BrandIdentity, BrandVisuals } from "@/lib/api/brand";
import { Button } from "@/components/ui/button";
import { Edit2, Globe, Building2, Palette } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { getContrastColor } from "@/lib/utils/colors";
import { config } from "@/lib/config";

interface BrandHeroSectionProps {
  identity: BrandIdentity;
  visuals?: BrandVisuals;
  onEdit: () => void;
  onEditVisuals: () => void;
}

export function HeaderSection({ identity, visuals, onEdit, onEditVisuals }: BrandHeroSectionProps) {
  // Check if we have extracted brand colors (custom-web or custom-logo)
  const isCustomBrand = visuals?.style_preset?.startsWith("custom");

  const getFullUrl = (path?: string) => {
    if (!path) return undefined;
    if (path.startsWith("http")) return path;
    return `${config.api.baseUrl}${path}`;
  };
  
  // Smart Color Calculation (High Contrast Enforcement)
  const bgColor = visuals?.background_color || '#ffffff';
  // If custom, we FORCE calculated contrast color. If not custom (card mode), we let system handle it (undefined)
  const textColor = isCustomBrand ? getContrastColor(bgColor) : undefined;
  
  // Chameleon Styles
  const containerStyle = isCustomBrand ? {
    backgroundColor: bgColor,
    color: textColor,
    borderColor: visuals?.primary_color ? `${visuals.primary_color}40` : undefined, // 25% opacity
  } : {};

  // Determine the best logo to display based on background contrast
  const getSmartLogo = () => {
      // 1. Determine background luminance/contrast
      // If isCustomBrand, we use the specific background color. If not, it's usually white/card.
      // But let's assume standard behavior: if text is white, bg is dark.
      const isDarkBg = textColor === "#ffffff";

      // 2. Access logos safely
      const logos = visuals?.logos;
      const legacyLogo = identity.logo_url;

      if (isDarkBg) {
          // Background is Dark -> Need Light/White Logo
          // Priority: DarkMode Logo (designed for dark bg) -> Secondary (Iso) -> Primary -> Legacy
          return logos?.dark_mode || logos?.secondary || logos?.primary || legacyLogo;
      } else {
          // Background is Light -> Need Dark/Color Logo
          // Priority: LightMode Logo (designed for light bg) -> Secondary (Iso) -> Primary -> Legacy
          return logos?.light_mode || logos?.secondary || logos?.primary || legacyLogo;
      }
  };

  const buttonStyle = isCustomBrand ? {
    backgroundColor: visuals?.primary_color,
    color: visuals?.primary_color ? getContrastColor(visuals.primary_color) : '#ffffff',
    borderColor: 'transparent'
  } : {};

  const displayLogo = getSmartLogo();

  return (
    <div 
      className={cn(
        "group relative rounded-xl p-8 shadow-sm transition-all duration-500 overflow-hidden",
        isCustomBrand ? "border-2" : "bg-card border border-border hover:shadow-md"
      )}
      style={containerStyle}
    >
      {/* Visual Identity Trigger (Top Center) */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 group-hover:translate-y-4 transition-transform duration-300 z-20">
         <Button 
            size="sm" 
            onClick={onEditVisuals}
            className="shadow-lg rounded-full px-4 h-8 text-xs font-medium"
            style={buttonStyle}
            variant={isCustomBrand ? "default" : "secondary"}
         >
            <Palette className="w-3.5 h-3.5 mr-2" />
            {isCustomBrand ? "ADN Detectado" : "Definir ADN Visual"}
         </Button>
      </div>

      {/* Edit Trigger */}
      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity z-10 flex gap-2">
        <Button size="sm" variant="secondary" onClick={onEdit} className="shadow-sm bg-background/50 backdrop-blur-sm">
          <Edit2 className="h-3.5 w-3.5 mr-2" />
          Editar Identidad
        </Button>
      </div>

      <div className="flex flex-col items-center text-center space-y-4 pt-4">
        {/* Logo Placeholder or Image */}
        <div 
            className={cn(
                "h-24 w-24 rounded-full flex items-center justify-center border-2 transition-colors relative bg-background/10 backdrop-blur-sm overflow-hidden",
                identity.logo_url ? "border-solid" : "border-dashed"
            )}
            style={{ 
                borderColor: isCustomBrand ? visuals?.primary_color : 'currentColor',
                color: isCustomBrand ? visuals?.primary_color : undefined
            }}
        >
           {displayLogo ? (
             // eslint-disable-next-line @next/next/no-img-element
             <img src={getFullUrl(displayLogo)} alt={identity.brand_name} className="h-full w-full object-contain p-2" />
           ) : (
             <span className="text-3xl font-bold">
               {identity.brand_name?.charAt(0) || "B"}
             </span>
           )}
        </div>

        <div className="space-y-2">
          <h1 
            className="text-3xl font-bold tracking-tight"
            style={{ fontFamily: visuals?.font_heading }}
          >
            {identity.brand_name || "Tu Marca"}
          </h1>
          
          <div className="flex flex-wrap justify-center gap-2">
            {identity.industry && (
              <Badge 
                variant="outline" 
                className="px-3 py-1 bg-primary/10 border-primary/20" 
                style={isCustomBrand ? { borderColor: 'currentColor', color: 'currentColor', opacity: 0.9 } : {}}
              >
                <Building2 className="h-3 w-3 mr-1" />
                {identity.industry}
              </Badge>
            )}
            
            {identity.website && (
              <a 
                href={identity.website} 
                target="_blank" 
                rel="noreferrer"
                className="inline-flex items-center px-3 py-1 text-xs font-medium rounded-full bg-muted/50 border border-border hover:bg-muted/80 transition-colors"
                style={isCustomBrand ? { borderColor: 'currentColor', color: 'currentColor', opacity: 0.9 } : {}}
              >
                <Globe className="h-3 w-3 mr-1" />
                {identity.website.replace(/^https?:\/\//, '')}
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Decorative Background (Subtle Gradient based on Primary) */}
      {isCustomBrand && visuals?.primary_color && (
          <div 
            className="absolute top-0 left-0 w-full h-full opacity-5 pointer-events-none -z-10"
            style={{ 
                background: `radial-gradient(circle at 50% 0%, ${visuals.primary_color}, transparent 70%)` 
            }} 
          />
      )}
    </div>
  );
}
