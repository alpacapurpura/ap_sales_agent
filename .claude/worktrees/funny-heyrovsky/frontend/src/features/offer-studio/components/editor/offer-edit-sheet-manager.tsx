import { 
  Sheet, 
  SheetContent, 
  SheetHeader, 
  SheetTitle, 
  SheetDescription,
} from "@/components/ui/sheet";
import { SECTION_REGISTRY } from "../../config/offer-builder-config";
import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface OfferEditSheetManagerProps {
  sectionId: string | null;
  isOpen: boolean;
  onClose: () => void;
  form: UseFormReturn<OfferFormValues>;
  onSave?: (sectionId: string) => Promise<void>;
  isSaving?: boolean;
}

export function OfferEditSheetManager({ 
  sectionId, 
  isOpen, 
  onClose, 
  form,
  onSave,
  isSaving = false
}: OfferEditSheetManagerProps) {
    if (!sectionId) return null;
    
    const config = SECTION_REGISTRY[sectionId];
    if (!config) return null;

    const FormComponent = config.formComponent;
    const Icon = config.icon;

    const handleSave = async (data?: any) => {
        if (data) {
            Object.entries(data).forEach(([key, value]) => {
                form.setValue(key as any, value);
            });
        }

        if (onSave && sectionId) {
            await onSave(sectionId);
        }
        onClose();
    };

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full sm:max-w-xl md:max-w-2xl p-0 flex flex-col h-full bg-background border-l shadow-2xl">
                <SheetHeader className="px-6 py-4 border-b bg-muted/10 flex-shrink-0 flex-row items-center justify-between space-y-0">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-md text-primary">
                            <Icon className="h-5 w-5" />
                        </div>
                        <div>
                            <SheetTitle className="text-lg">{config.title}</SheetTitle>
                            <SheetDescription className="text-xs">
                                Configura los detalles para esta sección de la oferta.
                            </SheetDescription>
                        </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
                        <X className="h-4 w-4" />
                        <span className="sr-only">Cerrar</span>
                    </Button>
                </SheetHeader>
                
                <div className="flex-1 overflow-y-auto px-6 py-6">
                    <div className="max-w-2xl mx-auto space-y-6">
                        <FormComponent 
                            form={form} 
                            defaultValues={form.getValues()}
                            onSave={handleSave}
                        />
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    );
}
