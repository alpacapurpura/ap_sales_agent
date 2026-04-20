import { ArrowRight, Clock } from "lucide-react";
import React, { createContext, useContext } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useLandingTheme } from "@/features/offer-studio/components/landing/context/LandingThemeContext";
import { cn } from "@/lib/utils";

// --- Context ---
type HeroLayout = "centered" | "split" | "background" | "vsl" | "urgency" | "quiz";

interface HeroContextValue {
  layout: HeroLayout;
  primaryColor: string;
}

const HeroContext = createContext<HeroContextValue | undefined>(undefined);

function useHeroContext() {
  const context = useContext(HeroContext);
  if (!context) {
    throw new Error("Hero components must be used within a Hero");
  }
  return context;
}

// --- Main Component ---
interface HeroProps extends React.HTMLAttributes<HTMLElement> {
  layout?: HeroLayout;
  bgImage?: string;
  children: React.ReactNode;
}

const HERO_LAYOUT_STYLES: Record<HeroLayout, string> = {
  centered: "relative py-24 px-6 text-center border-b border-slate-100 overflow-hidden bg-white",
  split: "relative py-24 px-6 overflow-hidden bg-white border-b border-slate-100",
  background:
    "relative min-h-[600px] flex items-center justify-center text-center px-6 overflow-hidden",
  vsl: "relative py-16 px-6 text-center bg-white border-b border-slate-100",
  urgency: "flex flex-col",
  quiz: "relative py-24 px-6 text-center bg-white",
};

const HERO_INNER_CONTAINER_CLASSES: Record<HeroLayout, string> = {
  split: "max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center",
  vsl: "max-w-4xl mx-auto space-y-8",
  quiz: "max-w-2xl mx-auto space-y-8 bg-white p-8 rounded-2xl shadow-xl border border-slate-100",
  background: "relative z-20 max-w-4xl mx-auto space-y-8 text-white",
  urgency: "",
  centered: "max-w-4xl mx-auto space-y-8 relative z-10",
};

function HeroBackgroundOverlays({
  layout,
  bgImage,
  primaryColor,
}: {
  layout: HeroLayout;
  bgImage?: string;
  primaryColor: string;
}) {
  if (layout === "background" && bgImage) {
    return (
      <>
        <div
          className="absolute inset-0 z-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${bgImage})` }}
        />
        <div className="absolute inset-0 bg-black/60 z-10" />
      </>
    );
  }
  if (layout === "centered") {
    return (
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{ backgroundColor: primaryColor }}
      />
    );
  }
  return null;
}

/**
 *
 */
function Hero({ layout = "centered", bgImage, className, children, ...props }: HeroProps) {
  const theme = useLandingTheme();
  const primaryColor = theme.primary_color || "#3b82f6";

  if (layout === "urgency") {
    return (
      <div className={cn("flex flex-col", className)} {...props}>
        <HeroContext.Provider value={{ layout, primaryColor }}>{children}</HeroContext.Provider>
      </div>
    );
  }

  return (
    <section className={cn(HERO_LAYOUT_STYLES[layout], className)} {...props}>
      <HeroContext.Provider value={{ layout, primaryColor }}>
        <HeroBackgroundOverlays layout={layout} bgImage={bgImage} primaryColor={primaryColor} />
        <div className={HERO_INNER_CONTAINER_CLASSES[layout]}>{children}</div>
      </HeroContext.Provider>
    </section>
  );
}

// --- Subcomponents ---

// 1. Content Wrapper
function Content({ className, children }: { className?: string; children: React.ReactNode }) {
  const { layout } = useHeroContext();

  return (
    <div
      className={cn(
        layout === "split"
          ? "space-y-8 text-left order-2 lg:order-1"
          : layout === "vsl"
            ? "space-y-4"
            : layout === "background"
              ? ""
              : "space-y-4",
        className,
      )}
    >
      {children}
    </div>
  );
}

// 2. Headline
interface HeadlineProps extends React.HTMLAttributes<HTMLHeadingElement> {
  as?: "h1" | "h2" | "h3";
}

function Headline({ className, children, as: Component = "h1", ...props }: HeadlineProps) {
  const { layout } = useHeroContext();

  const styles = {
    centered: "text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 leading-tight",
    split: "text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.1]",
    background: "text-5xl md:text-7xl font-extrabold tracking-tight leading-tight",
    vsl: "text-3xl md:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight",
    urgency: "text-4xl md:text-6xl font-black tracking-tight text-slate-900",
    quiz: "text-3xl md:text-4xl font-bold text-slate-900",
  };

  return (
    <Component className={cn(styles[layout], className)} {...props}>
      {children}
    </Component>
  );
}

// 3. Subheadline
function Subheadline({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  const { layout } = useHeroContext();

  const styles = {
    centered: "text-xl md:text-2xl text-slate-600 font-medium max-w-2xl mx-auto leading-relaxed",
    split: "text-lg md:text-xl text-slate-600 leading-relaxed max-w-lg",
    background: "text-xl md:text-2xl text-slate-200 max-w-2xl mx-auto font-light",
    vsl: "text-sm text-slate-500 italic",
    urgency: "text-xl text-slate-600 max-w-2xl mx-auto",
    quiz: "text-lg text-slate-600",
  };

  return (
    <p className={cn(styles[layout], className)} {...props}>
      {children}
    </p>
  );
}

// 4. CTA Wrapper & Button
interface CTAProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon?: boolean;
}

function CTA({ className, children, icon = true, ...props }: CTAProps) {
  const { layout, primaryColor } = useHeroContext();

  // Button specific styles
  const buttonStyles = {
    centered:
      "text-lg px-10 py-7 rounded-full shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all",
    split: "text-lg px-8 py-6 shadow-lg hover:shadow-xl transition-all",
    background:
      "text-lg px-10 py-7 rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition-all bg-white text-slate-900 hover:bg-slate-100 border-none",
    vsl: "w-full text-xl py-8 rounded-lg shadow-xl animate-pulse",
    urgency: "text-lg px-12 py-6 rounded-full",
    quiz: "p-4 rounded-lg border border-slate-200 hover:border-blue-500 hover:bg-blue-50 transition-all font-medium text-slate-700 flex justify-between items-center group w-full",
  };

  const style =
    layout !== "background" && layout !== "quiz" ? { backgroundColor: primaryColor } : {};

  return (
    <Button size="lg" className={cn(buttonStyles[layout], className)} style={style} {...props}>
      {children}{" "}
      {icon && (
        <ArrowRight
          className={cn(
            "ml-2",
            layout === "quiz"
              ? "w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-blue-500"
              : "w-5 h-5",
          )}
        />
      )}
    </Button>
  );
}

// 5. Media (Image/Video)
interface MediaProps {
  type: "image" | "video";
  src?: string;
  className?: string;
  alt?: string;
}

function Media({ type, src, className, alt }: MediaProps) {
  const { layout } = useHeroContext();

  if (layout === "vsl") {
    return (
      <div className="relative aspect-video bg-slate-900 rounded-xl overflow-hidden shadow-2xl mx-auto w-full max-w-3xl border-4 border-slate-100">
        {src ? (
          <iframe
            src={src}
            className="w-full h-full"
            allow="autoplay; fullscreen"
            allowFullScreen
          />
        ) : (
          <div className="flex items-center justify-center h-full text-white flex-col gap-4">
            <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
              <ArrowRight className="w-8 h-8 text-white" />
            </div>
            <span className="font-medium text-slate-400">Video Placeholder</span>
          </div>
        )}
      </div>
    );
  }

  if (layout === "split") {
    return (
      <div
        className={cn(
          "relative order-1 lg:order-2 h-[400px] lg:h-[600px] rounded-2xl overflow-hidden shadow-2xl rotate-1 hover:rotate-0 transition-transform duration-500",
          className,
        )}
      >
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${src})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-black/20 to-transparent pointer-events-none" />
      </div>
    );
  }

  return null;
}

// 6. Badge/Tag
function Tag({
  children,
  className,
  variant = "outline",
}: {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "secondary" | "destructive" | "outline";
}) {
  // Default variants per layout if not specified could be handled here, but sticking to passed props + defaults
  return (
    <Badge variant={variant} className={cn("mb-4", className)}>
      {children}
    </Badge>
  );
}

// 7. Scarcity/Urgency Bar
function Scarcity({ children, className }: { children: React.ReactNode; className?: string }) {
  const { layout } = useHeroContext();

  if (layout === "urgency") {
    return (
      <div className="bg-rose-600 text-white py-2 px-4 text-center font-bold text-sm md:text-base sticky top-0 z-50 shadow-md w-full">
        ⚠️ {children}
      </div>
    );
  }

  // For other layouts, it's usually a small pill
  return (
    <div
      className={cn(
        "flex items-center gap-2 text-sm font-medium px-3 py-1 rounded-full",
        layout === "background"
          ? "mt-6 justify-center text-slate-300 bg-black/30 w-fit mx-auto backdrop-blur-sm"
          : layout === "split"
            ? "text-amber-600 bg-amber-50 w-fit rounded-md"
            : "mt-2 justify-center text-slate-500 bg-slate-50 border border-slate-100",
        className,
      )}
    >
      <Clock className="w-4 h-4" />
      <span>{children}</span>
    </div>
  );
}

// 8. Actions Wrapper
function Actions({ children, className }: { children: React.ReactNode; className?: string }) {
  const { layout } = useHeroContext();
  const styles = {
    centered: "pt-8 flex flex-col items-center justify-center gap-4",
    split: "flex flex-col sm:flex-row gap-4 pt-4",
    background: "pt-8",
    vsl: "pt-6 max-w-xl mx-auto space-y-4",
    urgency: "pt-6",
    quiz: "grid gap-3 text-left mt-8",
  };

  return <div className={cn(styles[layout], className)}>{children}</div>;
}

// --- Export ---
Hero.Content = Content;
Hero.Headline = Headline;
Hero.Subheadline = Subheadline;
Hero.CTA = CTA;
Hero.Media = Media;
Hero.Tag = Tag;
Hero.Scarcity = Scarcity;
Hero.Actions = Actions;

export { Hero };
