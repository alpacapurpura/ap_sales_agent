"use client";

import { Sparkles, Bot } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { useActivePersonality } from "../../api/personality";

import { CloneUpload } from "./clone-upload";
import { DimensionSliders } from "./dimension-sliders";
import { PersonalityPreview } from "./personality-preview";
import { PresetCatalog } from "./preset-catalog";

export function PersonalityManager() {
  const params = useParams();
  const tenantId = (params?.tenantId as string) ?? "";
  const { data: profile } = useActivePersonality(tenantId);
  const [tab, setTab] = useState<string>("preset");

  return (
    <div className="space-y-8">
      {/* Selection tabs */}
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="w-full">
          <TabsTrigger value="preset" className="flex-1 gap-2">
            <Sparkles className="w-4 h-4" />
            Elegir personalidad
          </TabsTrigger>
          <TabsTrigger value="clone" className="flex-1 gap-2">
            <Bot className="w-4 h-4" />
            Clonar mi personalidad
          </TabsTrigger>
        </TabsList>

        <TabsContent value="preset" className="mt-4">
          <PresetCatalog onSelected={() => setTab("adjust")} />
        </TabsContent>

        <TabsContent value="clone" className="mt-4">
          <CloneUpload />
        </TabsContent>
      </Tabs>

      {/* Dimension fine-tuning + preview — only when a profile exists */}
      {profile && (
        <>
          <Separator />

          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-foreground mb-1">Ajuste fino</h3>
              <p className="text-xs text-muted-foreground">
                Calibra cada dimensión para que el agente se sienta exactamente como tú quieres.
              </p>
            </div>
            <DimensionSliders initialDimensions={profile.dimensions} />
          </div>

          <Separator />

          <PersonalityPreview profile={profile} />
        </>
      )}
    </div>
  );
}
