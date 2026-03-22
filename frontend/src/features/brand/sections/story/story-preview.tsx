import { BrandStory, BrandVisuals } from "@/features/brand/types";
import { History, Flag } from "lucide-react";

interface StorySectionProps {
    story: BrandStory;
    visuals: BrandVisuals;
    onEdit: () => void;
}

export function StorySection({ story, visuals, onEdit }: StorySectionProps) {
    const milestones = story?.milestones || [];
    const hasContent = story?.origin_story || milestones.length > 0;

    return (
        <section 
            onClick={onEdit}
            className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
        >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
                <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
                    <History className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-semibold uppercase tracking-wider">Historia de Origen</h3>
            </div>

            {!hasContent ? (
                <div className="pl-0 md:pl-14">
                    <p className="text-lg text-muted-foreground italic mb-2">
                        &quot;La gente no compra lo que haces, compra por qué lo haces.&quot;
                    </p>
                    <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                        <Flag className="w-4 h-4" />
                        Contar tu Historia
                    </span>
                </div>
            ) : (
                <div className="pl-0 md:pl-14 grid md:grid-cols-[1fr_250px] gap-12">
                    {/* Origin Story Text */}
                    <div className="prose prose-muted dark:prose-invert max-w-none">
                        <p className="text-sm leading-relaxed text-foreground whitespace-pre-line font-serif">
                            {story.origin_story}
                        </p>
                    </div>

                    {/* Timeline (Right side) */}
                    {milestones.length > 0 && (
                        <div className="border-l-2 border-border pl-6 space-y-8 relative py-2">
                            {milestones.map((milestone) => (
                                <div key={milestone.id} className="relative">
                                    <span className="absolute -left-[31px] top-1.5 h-3 w-3 rounded-full bg-muted-foreground/30 ring-4 ring-background group-hover:bg-primary transition-colors" />
                                    <span className="text-xs font-mono text-muted-foreground block mb-1 font-bold">{milestone.year}</span>
                                    <h4 className="font-medium text-foreground text-sm leading-snug">{milestone.title}</h4>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </section>
    );
}
