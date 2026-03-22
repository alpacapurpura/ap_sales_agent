import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ImagePlus } from "lucide-react";

interface EditableImageProps {
    src?: string;
    alt: string;
    onChange?: (newUrl: string) => void;
    className?: string;
    aspectRatio?: "video" | "square" | "portrait";
}

export function EditableImage({ src, alt, onChange, className, aspectRatio = "video" }: EditableImageProps) {
    const handleEdit = () => {
        if (!onChange) return;
        const url = prompt("Ingresa la nueva URL de la imagen:", src);
        if (url) onChange(url);
    };

    const ratioClasses = {
        video: "aspect-video",
        square: "aspect-square",
        portrait: "aspect-[3/4]"
    };

    return (
        <div className={cn("relative group overflow-hidden rounded-lg bg-slate-100", ratioClasses[aspectRatio], className)}>
            {src ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img 
                    src={src} 
                    alt={alt} 
                    className="w-full h-full object-cover"
                />
            ) : (
                <div className="flex items-center justify-center h-full text-slate-400">
                    <ImagePlus className="w-8 h-8" />
                </div>
            )}
            
            {onChange && (
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer" onClick={handleEdit}>
                    <Button variant="secondary" size="sm">
                        Cambiar Imagen
                    </Button>
                </div>
            )}
        </div>
    );
}
