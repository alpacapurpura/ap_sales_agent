import Image from "next/image";
import React from "react";

export interface AuthoritySectionProps {
  authority_image_url?: string;
  authority_name: string;
  authority_bio: string;
  story_hook?: string;
}

/**
 *
 */
export function AuthoritySection({
  authority_image_url,
  authority_name,
  authority_bio,
  story_hook,
}: AuthoritySectionProps) {
  return (
    <section className="py-16 px-6 bg-slate-900 text-white overflow-hidden">
      <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center gap-12">
        <div className="w-full md:w-1/3">
          {authority_image_url && (
            <Image
              src={authority_image_url}
              alt={authority_name}
              width={400}
              height={533}
              className="shadow-2xl ring-4 ring-white/10 rotate-3 transform hover:rotate-0 transition-all duration-500 rounded-lg w-full object-cover aspect-[3/4]"
              unoptimized
            />
          )}
        </div>
        <div className="w-full md:w-2/3 space-y-6">
          <div className="space-y-2">
            <p className="text-white/60 font-medium">Tu Mentora</p>
            <h3 className="text-3xl font-bold">{authority_name}</h3>
          </div>
          <p className="text-lg text-slate-300 leading-relaxed min-h-[150px]">{authority_bio}</p>

          {/* Story Hook if exists */}
          {story_hook && (
            <div className="mt-8 pt-8 border-t border-white/10">
              <h4 className="text-sm font-bold text-white/80 mb-2">Mi Historia</h4>
              <p className="text-slate-400 italic text-sm">{story_hook}</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
