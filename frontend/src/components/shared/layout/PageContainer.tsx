import { cn } from "@/lib/utils";

interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
  bare?: boolean;
}

/**
 *
 */
export function PageContainer({ children, className, bare = false }: PageContainerProps) {
  if (bare) {
    return <div className={cn("h-full", className)}>{children}</div>;
  }
  return <div className={cn("p-6 md:p-8 h-full", className)}>{children}</div>;
}
