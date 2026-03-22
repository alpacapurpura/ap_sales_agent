import React from 'react';
import { useLandingTheme } from '@/features/offer-studio/components/landing/context/LandingThemeContext';
import { getContrastColor } from '@/lib/utils/colors';

export interface PasGridSectionProps {
    problem_text: string;
    agitation_text: string;
    solution_text: string;
}

export function PasGridSection({ problem_text, agitation_text, solution_text }: PasGridSectionProps) {
    const theme = useLandingTheme();
    const primaryColor = theme.primary_color;
    const primaryTextColor = getContrastColor(primaryColor);

    return (
        <section className="py-16 px-6 bg-slate-50">
            <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8 text-center md:text-left">
                <div className="space-y-3 p-6 bg-white rounded-xl shadow-sm border border-slate-100">
                    <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600 font-bold mb-2">?</div>
                    <h3 className="font-bold text-lg">El Problema</h3>
                    <p className="text-slate-600 text-sm leading-relaxed min-h-[100px]">
                        {problem_text}
                    </p>
                </div>
                <div className="space-y-3 p-6 bg-white rounded-xl shadow-sm border border-slate-100">
                     <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 font-bold mb-2">!</div>
                    <h3 className="font-bold text-lg">La Agitación</h3>
                    <p className="text-slate-600 text-sm leading-relaxed min-h-[100px]">
                        {agitation_text}
                    </p>
                </div>
                <div className="space-y-3 p-6 rounded-xl shadow-sm border border-slate-100" style={{ backgroundColor: `${primaryColor}10` }}>
                     <div className="w-10 h-10 rounded-full flex items-center justify-center font-bold mb-2" style={{ backgroundColor: primaryColor, color: primaryTextColor }}>✓</div>
                    <h3 className="font-bold text-lg" style={{ color: primaryColor }}>La Solución</h3>
                    <p className="text-slate-700 text-sm leading-relaxed font-medium min-h-[100px]">
                        {solution_text}
                    </p>
                </div>
            </div>
        </section>
    );
}
