import { BrandIdentity } from "@/features/brand/types";
import { MessageSquare, Languages } from "lucide-react";

interface VoiceSectionProps {
  identity: BrandIdentity;
  onEdit: () => void;
}

export function VoiceSection({ identity, onEdit }: VoiceSectionProps) {
  return (
    <section
      onClick={onEdit}
      className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
          <MessageSquare className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">Voz & Comunicación</h3>
      </div>

      <div className="pl-0 md:pl-14">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-1 space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
              <Languages className="w-3 h-3" /> Idioma Principal
            </h4>
            <p className="text-2xl font-medium text-foreground capitalize">
              {identity.language || "Español"}
            </p>
          </div>

          <div className="md:col-span-3 space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
              Tono de Voz
            </h4>
            {identity.voice_tone ? (
              <p className="text-lg text-foreground italic">&quot;{identity.voice_tone}&quot;</p>
            ) : (
              <p className="text-lg text-muted-foreground italic opacity-50">
                &quot;Cercano, profesional y directo.&quot; (Sin definir)
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
