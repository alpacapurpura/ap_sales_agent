"use client";

import { TestimonialItem } from "@/lib/api/brand";
import { MessageSquareQuote, Plus, Video, Star, User } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

interface TestimonialsSectionProps {
  testimonials: TestimonialItem[];
  onEdit: (item?: TestimonialItem) => void;
}

export function TestimonialsSection({ testimonials, onEdit }: TestimonialsSectionProps) {
  const hasContent = testimonials && testimonials.length > 0;

  return (
    <section 
        className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors cursor-pointer" onClick={() => onEdit()}>
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
            <MessageSquareQuote className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">Testimonios & Social Proof</h3>
      </div>

      {!hasContent ? (
        <div className="pl-0 md:pl-14 cursor-pointer" onClick={() => onEdit()}>
            <p className="text-lg text-muted-foreground italic mb-2">
                &quot;Lo que dicen tus clientes es tu mejor venta. ¿Qué opinan de ti?&quot;
            </p>
            <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Añadir Testimonios
            </span>
        </div>
      ) : (
        <div className="pl-0 md:pl-14">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {testimonials.map((item) => (
                    <div 
                        key={item.id} 
                        className="group/card relative bg-card border rounded-lg p-5 hover:shadow-md transition-all cursor-pointer flex flex-col gap-4"
                        onClick={() => onEdit(item)}
                    >
                        {/* Rating */}
                        <div className="flex gap-0.5">
                            {Array.from({ length: item.rating || 5 }).map((_, i) => (
                                <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                            ))}
                        </div>

                        {/* Content */}
                        <div className="flex-1">
                            {item.type === 'video' ? (
                                <div className="aspect-video w-full bg-muted rounded-md flex items-center justify-center mb-2">
                                    <Video className="w-8 h-8 text-muted-foreground" />
                                </div>
                            ) : (
                                <p className="text-sm text-foreground/90 italic line-clamp-4">
                                    &quot;{item.content}&quot;
                                </p>
                            )}
                        </div>

                        {/* Author */}
                        <div className="flex items-center gap-3 mt-auto pt-4 border-t border-border/50">
                            <Avatar className="h-8 w-8">
                                <AvatarImage src={item.author_avatar} />
                                <AvatarFallback>
                                    <User className="h-4 w-4" />
                                </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">{item.author_name}</p>
                                <p className="text-xs text-muted-foreground truncate">{item.author_role}</p>
                            </div>
                            {item.type === 'video' && (
                                <Badge variant="secondary" className="text-[10px] h-5 px-1.5">
                                    Video
                                </Badge>
                            )}
                        </div>
                    </div>
                ))}
                
                 {/* Add New Trigger (Visual) */}
                 <div className="flex flex-col items-center justify-center text-center group/add cursor-pointer min-h-[200px] border-2 border-dashed border-muted-foreground/20 rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-colors" onClick={() => onEdit()}>
                    <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-3 group-hover/add:bg-primary/10 transition-colors">
                        <Plus className="w-5 h-5 text-muted-foreground group-hover/add:text-primary" />
                    </div>
                    <span className="text-sm font-medium text-muted-foreground group-hover/add:text-primary">Agregar Testimonio</span>
                </div>
            </div>
        </div>
      )}
    </section>
  );
}
