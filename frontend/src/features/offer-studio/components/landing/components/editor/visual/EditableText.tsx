import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

import type React from "react";

interface EditableTextProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
  placeholder?: string;
  as?: React.ElementType; // Allow polymorphic prop to pass through (ignored for now)
}

/**
 *
 */
export function EditableText({ value, onChange, className, placeholder, as }: EditableTextProps) {
  const [localValue, setLocalValue] = useState(value || "");

  // Sync local buffer when the prop changes externally (e.g. parent form reset).
  // This legitimately mirrors an external prop into local editable state.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
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
        className,
      )}
    />
  );
}
