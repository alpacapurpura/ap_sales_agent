import { useAuth } from "@clerk/nextjs";
import { usePuck } from "@puckeditor/core";
import { Wand2, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { offerApi } from "@/features/offer-studio/api";

interface AiRemixButtonProps {
  offerId: string;
}

export function AiRemixButton({ offerId }: AiRemixButtonProps) {
  const { appState, dispatch } = usePuck();
  const { getToken } = useAuth();

  const [isOpen, setIsOpen] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Get selected item
  const { itemSelector } = appState.ui;
  const selectedItem = itemSelector
    ? appState.data.content.find((item) => item.props.id === itemSelector.index)
    : null;

  // If no item selected or multiple, don't show (or show disabled)
  // Note: itemSelector.index is actually the ID in Puck v0.14? Or the index?
  // Let's check Puck docs or assume ID based on typical usage.
  // Usually itemSelector is { index: number, zone: string }.
  // If we use ID in props, we might need to look it up by index.
  const selectedBlock = itemSelector !== null && appState.data.content[itemSelector.index];

  if (!selectedBlock) return null;

  const handleRemix = async () => {
    setIsLoading(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");

      // Call Backend
      const newProps = await offerApi.regenerateBlock(
        offerId,
        selectedBlock.type,
        selectedBlock.props,
        instruction,
        token,
      );

      // Update Puck State
      dispatch({
        type: "replace",
        destinationIndex: itemSelector.index,
        destinationZone: itemSelector.zone!,
        data: {
          ...selectedBlock,
          props: {
            ...selectedBlock.props, // Keep ID and other internal props
            ...newProps, // Overwrite content
          },
        },
      });

      // Also trigger a save if needed, or let user save manually
      toast.success("Sección regenerada con éxito");
      setIsOpen(false);
    } catch (error) {
      console.error(error);
      toast.error("Error al regenerar la sección");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="gap-2 text-indigo-600 border-indigo-200 hover:bg-indigo-50"
        >
          <Wand2 className="w-4 h-4" />
          AI Remix: {selectedBlock.type.replace("Section", "")}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Regenerar Sección con IA</DialogTitle>
          <DialogDescription>
            Da instrucciones para mejorar esta sección. La IA usará el contexto de tu marca y
            oferta.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <Textarea
            placeholder="Ej: Hazlo más persuasivo, enfócate en la urgencia..."
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            rows={4}
          />
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setIsOpen(false)}>
            Cancelar
          </Button>
          <Button
            onClick={handleRemix}
            disabled={isLoading}
            className="bg-indigo-600 hover:bg-indigo-700"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Wand2 className="w-4 h-4 mr-2" />
            )}
            Regenerar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
