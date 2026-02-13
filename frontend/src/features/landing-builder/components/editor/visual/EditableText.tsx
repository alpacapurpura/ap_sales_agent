import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

interface EditableTextProps {
    value: string;
    onChange: (value: string) => void;
    className?: string;
    placeholder?: string;
}

export function EditableText({ value, onChange, className, placeholder }: EditableTextProps) {
    const [localValue, setLocalValue] = useState(value || "");

    useEffect(() => {
        setLocalValue(value || "");
    }, [value]);

    const handleBlur = () => {
        if (localValue !== value) {
            onChange(localValue);
        }
    };

    return (
        <input
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            onBlur={handleBlur}
            placeholder={placeholder}
            className={cn(
                "bg-transparent border-none outline-none w-full focus:ring-2 focus:ring-primary/20 rounded px-1 -mx-1 transition-all hover:bg-black/5",
                className
            )}
        />
    );
}
