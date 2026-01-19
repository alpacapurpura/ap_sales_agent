"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CreateAvatarDTO } from "@/lib/api/avatar";
import { Loader2, Save } from "lucide-react";

interface AvatarFormProps {
  initialData?: Partial<CreateAvatarDTO>;
  onSubmit: (data: CreateAvatarDTO) => Promise<void>;
  isSubmitting?: boolean;
}

export function AvatarForm({ initialData, onSubmit, isSubmitting = false }: AvatarFormProps) {
  const [formData, setFormData] = useState<CreateAvatarDTO>({
    name: initialData?.name || "",
    icp_description: initialData?.icp_description || "",
    anti_avatar: initialData?.anti_avatar || "",
    scope: "GLOBAL"
  });

  const handleChange = (field: keyof CreateAvatarDTO, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card>
        <CardHeader>
          <CardTitle>Configuración del Avatar</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Nombre del Avatar</Label>
            <Input
              id="name"
              placeholder="Ej: Emprendedores Tech"
              value={formData.name}
              onChange={(e) => handleChange("name", e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="icp">Descripción del Cliente Ideal (ICP)</Label>
            <Textarea
              id="icp"
              placeholder="Describe al cliente perfecto: demografía, dolores, deseos..."
              className="min-h-[150px]"
              value={formData.icp_description}
              onChange={(e) => handleChange("icp_description", e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="anti_avatar">Anti-Avatar</Label>
            <Textarea
              id="anti_avatar"
              placeholder="¿A quién NO queremos venderle?"
              value={formData.anti_avatar}
              onChange={(e) => handleChange("anti_avatar", e.target.value)}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button type="submit" disabled={isSubmitting || !formData.name}>
            {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            Guardar Avatar
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
