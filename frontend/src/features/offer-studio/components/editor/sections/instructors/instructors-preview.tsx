import React from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { OfferFormValues } from "../../../../types/schema";
import { useFormContext } from "react-hook-form";
import { User, UserX } from "lucide-react";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";

interface InstructorsPreviewProps {
  data?: Partial<OfferFormValues>;
}

export const InstructorsPreview = ({ data: propsData }: InstructorsPreviewProps) => {
  const form = useFormContext<OfferFormValues>();
  const data = propsData || (form ? form.watch() : null);
  const { settings } = useBrandSettings();

  if (!data?.instructors?.length) return null;

  const { instructors } = data;
  const team = settings?.team || [];

  return (
    <div className="w-full">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {instructors.map((instructorId, idx) => {
          const instructor = team.find((member) => member.id === instructorId);

          if (!instructor) {
            return (
              <div
                key={idx}
                className="flex flex-col items-center text-center p-3 rounded-xl bg-muted/20 border border-transparent border-dashed"
              >
                <Avatar className="h-14 w-14 mb-2 ring-2 ring-muted shadow-sm opacity-50">
                  <AvatarFallback className="bg-muted text-muted-foreground">
                    <UserX className="h-6 w-6" />
                  </AvatarFallback>
                </Avatar>
                <div className="w-full px-1 opacity-50">
                  <p className="text-xs font-semibold truncate text-foreground/90">Desconocido</p>
                  <p className="text-[10px] text-muted-foreground truncate font-mono opacity-70">
                    ID: {instructorId.slice(0, 8)}...
                  </p>
                </div>
              </div>
            );
          }

          return (
            <div
              key={instructor.id}
              className="flex flex-col items-center text-center p-3 rounded-xl bg-muted/20 border border-transparent hover:border-border/50 transition-colors"
            >
              <Avatar className="h-14 w-14 mb-2 ring-2 ring-background shadow-sm">
                <AvatarImage
                  src={instructor.headshot_url}
                  alt={instructor.name}
                  className="object-cover"
                />
                <AvatarFallback className="bg-primary/10 text-primary">
                  <User className="h-6 w-6" />
                </AvatarFallback>
              </Avatar>
              <div className="w-full px-1">
                <p className="text-xs font-semibold truncate text-foreground/90">
                  {instructor.name}
                </p>
                <p className="text-[10px] text-muted-foreground truncate font-medium opacity-80">
                  {instructor.role}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
