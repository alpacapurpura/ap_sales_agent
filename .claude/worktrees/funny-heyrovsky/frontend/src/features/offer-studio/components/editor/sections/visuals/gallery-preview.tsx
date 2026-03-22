import React from 'react';
import { OfferFormValues } from '../../../../types/schema';
import { useFormContext } from 'react-hook-form';
import { Play } from 'lucide-react';
import { AssetType } from '../../../../types';

interface GalleryPreviewProps {
  data?: Partial<OfferFormValues>;
}

export const GalleryPreview = ({ data: propsData }: GalleryPreviewProps) => {
  const form = useFormContext<OfferFormValues>();
  const data = propsData || (form ? form.watch() : null);

  const { assets } = data || {};
  
  const media = assets?.filter(a => 
    [AssetType.IMAGE, AssetType.VIDEO].includes(a.type as AssetType)
  ) || [];

  if (!media.length) return null;

  return (
    <div className="w-full grid grid-cols-2 md:grid-cols-3 gap-2">
      {media.map((item, idx) => (
        <div key={idx} className="group relative aspect-square rounded-lg overflow-hidden bg-muted cursor-zoom-in">
            {item.type === AssetType.IMAGE ? (
                <img 
                    src={item.url} 
                    alt={item.name} 
                    className="object-cover w-full h-full transition-transform duration-500 group-hover:scale-110"
                />
            ) : (
                <div className="w-full h-full flex items-center justify-center bg-slate-900">
                    <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/30 transition-colors">
                        <Play className="w-4 h-4 text-white fill-white ml-0.5" />
                    </div>
                </div>
            )}
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
        </div>
      ))}
    </div>
  );
};
