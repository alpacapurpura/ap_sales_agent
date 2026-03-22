import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

interface LeadAvatarProps {
  src?: string;
  initials?: string;
  alt?: string;
  className?: string;
}

export function LeadAvatar({ src, initials, alt, className }: LeadAvatarProps) {
  return (
    <Avatar className={cn("h-10 w-10 border border-border", className)}>
      <AvatarImage src={src} alt={alt || "Lead Avatar"} />
      <AvatarFallback className="bg-primary/10 text-primary font-medium text-sm">
        {initials?.slice(0, 2).toUpperCase() || "??"}
      </AvatarFallback>
    </Avatar>
  );
}
