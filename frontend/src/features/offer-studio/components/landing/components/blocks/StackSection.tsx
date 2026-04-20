import React from "react";

export interface ModuleItem {
  title: string;
  description: string;
}

export interface StackSectionProps {
  modules: ModuleItem[];
}

/**
 *
 */
export function StackSection({ modules = [] }: StackSectionProps) {
  const items = modules || [];

  return (
    <section className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Lo que vas a lograr semana a semana</h2>
          <p className="text-slate-600">Un sistema probado paso a paso</p>
        </div>

        <div className="grid gap-6">
          {items.length === 0 ? (
            <div className="text-center p-8 border-2 border-dashed border-slate-200 rounded-xl text-slate-400">
              No hay módulos configurados. Añade uno en el panel lateral.
            </div>
          ) : (
            items.map((mod, i) => (
              <div
                key={i}
                className="flex gap-4 p-6 rounded-xl border border-slate-100 hover:shadow-md transition-shadow bg-white"
              >
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-xl">
                  {i + 1}
                </div>
                <div className="flex-1 space-y-1">
                  <h4 className="font-bold text-lg text-slate-900">{mod.title}</h4>
                  <p className="text-slate-600 text-sm">{mod.description}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
