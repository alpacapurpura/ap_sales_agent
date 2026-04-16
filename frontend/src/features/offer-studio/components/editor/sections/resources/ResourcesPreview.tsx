import { FileText, Link as LinkIcon, Headphones, Download } from "lucide-react";
import React from "react";
import { useFormContext } from "react-hook-form";

import { AssetType } from "../../../../types";

import type { OfferFormValues } from "../../../../types/schema";

interface ResourcesPreviewProps {
  data?: Partial<OfferFormValues>;
}

export const ResourcesPreview = ({ data: propsData }: ResourcesPreviewProps) => {
  const form = useFormContext<OfferFormValues>();
  const data = propsData || (form ? form.watch() : null);

  const { assets } = data || {};

  const resources =
    assets?.filter((a) =>
      [AssetType.PDF, AssetType.TXT, AssetType.URL, AssetType.AUDIO].includes(a.type as AssetType),
    ) || [];

  if (!resources.length) return null;

  const getIcon = (type: AssetType) => {
    switch (type) {
      case AssetType.PDF:
        return <FileText className="w-4 h-4 text-rose-500" />;
      case AssetType.TXT:
        return <FileText className="w-4 h-4 text-slate-500" />;
      case AssetType.AUDIO:
        return <Headphones className="w-4 h-4 text-violet-500" />;
      case AssetType.URL:
        return <LinkIcon className="w-4 h-4 text-sky-500" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  return (
    <div className="w-full grid grid-cols-1 gap-2">
      {resources.map((resource, idx) => (
        <div
          key={idx}
          className="flex items-center gap-3 p-3 rounded-lg border border-transparent hover:bg-muted/30 hover:border-border/40 transition-all group"
        >
          <div className="h-8 w-8 flex items-center justify-center bg-muted/50 rounded-md group-hover:bg-background transition-colors shadow-sm">
            {getIcon(resource.type as AssetType)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate text-foreground/90">{resource.name}</p>
            <p className="text-[10px] text-muted-foreground truncate opacity-70">
              {resource.type} • {resource.url}
            </p>
          </div>
          <div className="opacity-0 group-hover:opacity-100 transition-opacity">
            <Download className="w-4 h-4 text-muted-foreground" />
          </div>
        </div>
      ))}
    </div>
  );
};
