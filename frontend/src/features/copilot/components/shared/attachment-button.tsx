"use client";

import { Paperclip } from "lucide-react";
import { forwardRef, useRef } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface AttachmentButtonProps extends Omit<
  React.ButtonHTMLAttributes<HTMLButtonElement>,
  "onClick"
> {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  accept?: string;
}

export const AttachmentButton = forwardRef<HTMLButtonElement, AttachmentButtonProps>(
  (
    {
      onFilesSelected,
      disabled = false,
      accept = ".pdf,.docx,.txt,.md,.pptx",
      className,
      ...props
    },
    ref,
  ) => {
    const inputRef = useRef<HTMLInputElement>(null);

    const handleClick = () => {
      inputRef.current?.click();
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const fileList = e.target.files;
      if (!fileList || fileList.length === 0) return;

      const files = Array.from(fileList);
      onFilesSelected(files);

      // Reset input value so the same file can be re-selected
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    };

    return (
      <>
        <Button
          ref={ref}
          type="button"
          variant="ghost"
          size="icon"
          onClick={handleClick}
          disabled={disabled}
          aria-label="Adjuntar documento"
          className={cn("shrink-0", className)}
          {...props}
        >
          <Paperclip className="h-4 w-4" />
        </Button>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept}
          onChange={handleChange}
          className="hidden"
          tabIndex={-1}
          aria-hidden="true"
        />
      </>
    );
  },
);
AttachmentButton.displayName = "AttachmentButton";
