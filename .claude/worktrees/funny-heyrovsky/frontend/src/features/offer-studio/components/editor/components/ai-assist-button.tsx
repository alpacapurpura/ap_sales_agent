import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sparkles, Loader2, Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface AIAssistButtonProps {
    onGenerate: () => Promise<void>;
    isDisabled?: boolean;
    disabledReason?: string;
    label?: string;
    className?: string;
}

export function AIAssistButton({ 
    onGenerate, 
    isDisabled = false, 
    disabledReason = "Complete los requisitos previos", 
    label = "Ayuda IA",
    className
}: AIAssistButtonProps) {
    const [loading, setLoading] = useState(false);

    const handleClick = async (e: React.MouseEvent) => {
        e.preventDefault(); // Prevent form submission if inside a form
        if (isDisabled || loading) return;
        setLoading(true);
        try {
            await onGenerate();
        } finally {
            setLoading(false);
        }
    };

    const button = (
        <Button 
            type="button" 
            variant="outline" 
            size="sm" 
            onClick={handleClick} 
            disabled={isDisabled || loading}
            className={cn(
                "bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border-indigo-200 dark:bg-indigo-950/30 dark:text-indigo-300 dark:border-indigo-800 transition-all", 
                className
            )}
        >
            {loading ? <Loader2 className="w-3 h-3 mr-2 animate-spin" /> : <Sparkles className="w-3 h-3 mr-2" />}
            {label}
        </Button>
    );

    if (isDisabled) {
        return (
            <TooltipProvider>
                <Tooltip delayDuration={100}>
                    <TooltipTrigger asChild>
                        {/* Wrapper span required for tooltip on disabled elements */}
                        <span tabIndex={0} className="cursor-not-allowed inline-flex opacity-60 grayscale">
                            {button}
                        </span>
                    </TooltipTrigger>
                    <TooltipContent className="bg-destructive text-destructive-foreground">
                        <p className="flex items-center gap-2 text-xs font-semibold">
                            <Info className="w-3 h-3" />
                            {disabledReason}
                        </p>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        );
    }

    return button;
}
