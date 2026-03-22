import React, { createContext, useContext } from "react";
import { Button } from "@/components/ui/button";
import { Edit3, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

// --- Context ---
interface OfferSectionContextValue {
  onEdit?: () => void;
  isEmpty?: boolean;
}

const OfferSectionContext = createContext<OfferSectionContextValue | undefined>(undefined);

function useOfferSection() {
  const context = useContext(OfferSectionContext);
  if (!context) {
    throw new Error("OfferSection subcomponents must be used within an OfferSection");
  }
  return context;
}

// --- Main Component ---
interface OfferSectionProps extends React.HTMLAttributes<HTMLElement> {
  children: React.ReactNode;
  onEdit?: () => void;
  isEmpty?: boolean;
}

function OfferSection({
  children,
  className,
  onEdit,
  isEmpty,
  ...props
}: OfferSectionProps) {
  return (
    <OfferSectionContext.Provider value={{ onEdit, isEmpty }}>
      <section
        onClick={onEdit}
        className={cn(
          "group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer scroll-mt-24",
          className
        )}
        {...props}
      >
        {children}
      </section>
    </OfferSectionContext.Provider>
  );
}

// --- Subcomponents ---

interface OfferSectionHeaderProps {
  title: string;
  icon?: React.ElementType;
  description?: string;
  className?: string;
}

function OfferSectionHeader({
  title,
  icon: Icon,
  description,
  className,
}: OfferSectionHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors",
        className
      )}
    >
      {Icon && (
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 group-hover:shadow-sm transition-all duration-300">
          <Icon className="h-5 w-5" />
        </div>
      )}
      <div className="flex flex-col">
        <h3 className="text-sm font-semibold uppercase tracking-wider">{title}</h3>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
    </div>
  );
}

interface OfferSectionContentProps {
  children: React.ReactNode;
  className?: string;
}

function OfferSectionContent({ children, className }: OfferSectionContentProps) {
  return <div className={cn("pl-0 md:pl-14", className)}>{children}</div>;
}

interface OfferSectionEmptyStateProps {
  quote?: string;
  actionLabel?: string;
  className?: string;
}

function OfferSectionEmptyState({
  quote = "Define este aspecto para potenciar tu oferta.",
  actionLabel = "Completar Sección",
  className,
}: OfferSectionEmptyStateProps) {
  return (
    <div className={cn("pl-0 md:pl-14", className)}>
      <p className="text-lg text-muted-foreground italic mb-2">&quot;{quote}&quot;</p>
      <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
        <Sparkles className="w-4 h-4" />
        {actionLabel}
      </span>
    </div>
  );
}

interface OfferSectionControlsProps {
  className?: string;
}

function OfferSectionControls({ className }: OfferSectionControlsProps) {
  // We can use onEdit from context if needed, but the main section usually handles the click.
  // However, keeping the button here for specific actions or just visual representation.
  return (
    <div
      className={cn(
        "absolute top-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity",
        className
      )}
    >
      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
        <Edit3 className="h-4 w-4" />
      </Button>
    </div>
  );
}

// --- Attach Subcomponents ---
const OfferSectionNamespace = Object.assign(OfferSection, {
  Header: OfferSectionHeader,
  Content: OfferSectionContent,
  EmptyState: OfferSectionEmptyState,
  Controls: OfferSectionControls,
});

export { OfferSectionNamespace as OfferSection };
