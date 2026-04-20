import React from "react";

export interface SolutionSectionProps {
  method_name: string;
  method_description: string;
}

/**
 *
 */
export function SolutionSection({ method_name, method_description }: SolutionSectionProps) {
  return (
    <section className="py-20 px-6 text-center">
      <div className="max-w-3xl mx-auto space-y-6">
        <h2 className="text-sm font-bold tracking-widest uppercase text-slate-400">Presentando</h2>
        <h2 className="text-4xl md:text-5xl font-serif font-bold text-slate-900 text-center">
          {method_name}
        </h2>
        <p className="text-xl text-slate-600 leading-relaxed text-center">{method_description}</p>
      </div>
    </section>
  );
}
