import React from 'react';

interface PlaceholderPreviewProps {
  sectionId: string;
  title?: string;
}

export const PlaceholderPreview = ({ sectionId, title }: PlaceholderPreviewProps) => {
  return (
    <div className="w-full h-full min-h-[120px] rounded-xl border-2 border-dashed border-muted-foreground/10 bg-muted/5 flex flex-col items-center justify-center p-4 text-center">
      <div className="text-sm font-medium text-foreground/80 mb-1">
        {title || "Sección Vacía"}
      </div>
      <div className="text-xs text-muted-foreground">
        Preview: {sectionId}
      </div>
    </div>
  );
};
