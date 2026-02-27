import { cn } from "@/lib/utils";

interface ${ComponentName}Props extends React.HTMLAttributes<HTMLDivElement> {
  // Add custom props here
}

export function ${ComponentName}({ className, ...props }: ${ComponentName}Props) {
  return (
    <div className={cn("", className)} {...props}>
      {/* Component content */}
    </div>
  );
}
