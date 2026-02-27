import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface BentoGridProps {
  children: React.ReactNode;
  className?: string;
}

export function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 md:grid-cols-3 gap-4 p-4",
        "auto-rows-[minmax(180px,auto)]", // Dynamic row height
        className
      )}
    >
      {children}
    </div>
  );
}

export function BentoCard({
  title,
  children,
  className,
  colSpan = 1,
  rowSpan = 1,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  colSpan?: number;
  rowSpan?: number;
}) {
  return (
    <Card
      className={cn(
        "group relative overflow-hidden transition-all hover:shadow-md",
        colSpan === 2 && "md:col-span-2",
        colSpan === 3 && "md:col-span-3",
        rowSpan === 2 && "md:row-span-2",
        className
      )}
    >
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground group-hover:text-primary transition-colors">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-full w-full">{children}</ScrollArea>
      </CardContent>
    </Card>
  );
}
