"use client";

import { TestimonialItem } from "@/features/brand/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2, Edit2, Video, AlignLeft } from "lucide-react";

interface TestimonialsListProps {
  items: TestimonialItem[];
  onEdit: (item: TestimonialItem) => void;
  onDelete: (id: string) => void;
}

export function TestimonialsList({ items, onEdit, onDelete }: TestimonialsListProps) {
  if (items.length === 0) {
    return (
      <div className="col-span-full text-center p-10 text-muted-foreground border-2 border-dashed rounded-lg bg-muted/10">
        No hay testimonios registrados.
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      {items.map((item) => (
        <Card
          key={item.id}
          className="group cursor-pointer border hover:border-primary transition-all bg-background shadow-sm hover:shadow-md relative"
          onClick={() => onEdit(item)}
        >
          <CardContent className="p-6 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="flex items-start space-x-4 flex-1">
              <div className="p-2 bg-primary/10 rounded-full flex-shrink-0">
                {item.type === "video" ? (
                  <Video className="h-5 w-5 text-primary" />
                ) : (
                  <AlignLeft className="h-5 w-5 text-primary" />
                )}
              </div>
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold">{item.author_name}</h4>
                  <Badge variant="outline" className="text-[10px] h-5 px-1.5">
                    {item.type === "video" ? "Video" : "Texto"}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{item.author_role}</p>
                <p className="text-xs text-muted-foreground mt-2 line-clamp-2 italic border-l-2 pl-2 border-primary/20">
                  {item.content}
                </p>
              </div>
            </div>
            <div
              className="flex items-center border rounded-md bg-background flex-shrink-0"
              onClick={(e) => e.stopPropagation()}
            >
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-none border-r"
                onClick={() => onEdit(item)}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-none text-destructive hover:text-destructive"
                onClick={() => onDelete(item.id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
