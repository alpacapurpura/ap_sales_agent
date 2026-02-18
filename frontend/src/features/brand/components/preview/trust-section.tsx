import { BrandIdentity, AuthorityItem, BrandVisuals } from "@/features/brand/types";
import { Award, ExternalLink, PlusCircle } from "lucide-react";
import Image from "next/image";

interface TrustSectionProps {
  identity: BrandIdentity;
  authority: AuthorityItem[];
  visuals: BrandVisuals;
  onEditIdentity: () => void;
  onEditAuthority: (item?: any) => void;
}

export function TrustSection({ identity, authority, visuals, onEditIdentity, onEditAuthority }: TrustSectionProps) {
  // Helpers
  const AuthorityBadge = ({ item }: { item: AuthorityItem }) => (
    <div 
        onClick={(e) => { e.stopPropagation(); onEditAuthority(item); }}
        className="flex items-center gap-3 p-3 rounded-lg border border-transparent hover:border-border hover:bg-muted/30 transition-all cursor-pointer group/badge"
    >
        <div className="h-12 w-12 rounded bg-muted flex items-center justify-center text-xs font-bold text-muted-foreground overflow-hidden shrink-0">
            {item.logo_url ? (
                <img 
                    src={item.logo_url} 
                    alt={item.entity_name} 
                    className="h-full w-full object-cover" 
                />
            ) : (
                item.entity_name.substring(0,2)
            )}
        </div>
        <div className="flex-1 min-w-0">
            <h5 className="text-sm font-medium text-foreground truncate group-hover/badge:text-primary transition-colors">{item.entity_name}</h5>
            <p className="text-xs text-muted-foreground truncate">{item.context || item.type}</p>
        </div>
        {item.proof_url && <ExternalLink className="w-3 h-3 text-muted-foreground ml-2 opacity-0 group-hover/badge:opacity-50 transition-opacity" />}
    </div>
  );

  return (
    <section className="pt-8 border-t border-border">
        {/* Authority Vault (Centered & Expanded) */}
        <div className="max-w-3xl mx-auto">
             <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-md bg-amber-500/10 text-amber-600">
                        <Award className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold uppercase tracking-wider">Autoridad & Prensa</h3>
                        <p className="text-xs text-muted-foreground">Premios, certificaciones y menciones en medios.</p>
                    </div>
                </div>
                
                <button 
                    onClick={() => onEditAuthority()}
                    className="text-xs flex items-center gap-1.5 text-muted-foreground hover:text-primary transition-colors px-3 py-1.5 rounded-full hover:bg-muted"
                >
                    <PlusCircle className="w-3.5 h-3.5" />
                    <span>Agregar</span>
                </button>
            </div>
            
            <div className="bg-card rounded-xl border border-border/50 shadow-sm p-2">
                {authority && authority.length > 0 ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {authority.map(item => (
                            <AuthorityBadge key={item.id} item={item} />
                        ))}
                    </div>
                ) : (
                    <div 
                        onClick={() => onEditAuthority()}
                        className="flex flex-col items-center justify-center py-12 text-center cursor-pointer hover:bg-muted/20 rounded-lg transition-colors border border-dashed border-transparent hover:border-muted-foreground/20"
                    >
                        <Award className="w-10 h-10 text-muted-foreground/20 mb-3" />
                        <p className="text-sm font-medium text-foreground/80">Sin elementos de autoridad</p>
                        <p className="text-xs text-muted-foreground max-w-xs mt-1">
                            Agrega premios, certificaciones o apariciones en prensa para aumentar la confianza.
                        </p>
                    </div>
                )}
            </div>
        </div>
    </section>
  );
}
