"use client";

import type { Data } from "@puckeditor/core";

import { Puck } from "@puckeditor/core";

import "@puckeditor/core/dist/index.css";

import { useAuth } from "@clerk/nextjs";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { offerApi } from "@/features/offer-studio/api";

import { transformConfigToPuckData } from "../../utils/adapter";
import { config } from "../../utils/puck.config";

import { AiRemixButton } from "./AiRemixButton";

import type { RootProps, Props } from "../../utils/puck.config";
import type { LandingPageConfig } from "@/features/offer-studio/components/landing/types/schema";

interface PuckEditorProps {
  initialConfig: LandingPageConfig;
  offerId: string;
}

/**
 *
 */
export function PuckEditor({ initialConfig, offerId }: PuckEditorProps) {
  const { getToken } = useAuth();
  const params = useParams();
  const tenantId = params?.tenantId as string;

  // Initialize Data
  const [data] = useState<Data<Props, RootProps>>(() => {
    // Check if content is already Puck Data (has root and content array)
    const content = initialConfig.content as Record<string, unknown> | undefined;
    if (content?.root && Array.isArray(content.content)) {
      return content as unknown as Data<Props, RootProps>;
    }
    // Otherwise transform from TransformerContent
    try {
      return transformConfigToPuckData(initialConfig);
    } catch (e) {
      console.error("Error transforming data:", e);
      // Fallback empty data
      return {
        root: { props: { theme: initialConfig.theme } },
        content: [],
        zones: {},
      } as unknown as Data<Props, RootProps>;
    }
  });

  const handleSave = async (newData: Data<Props, RootProps>) => {
    const token = await getToken();
    if (!token) {
      toast.error("No autenticado");
      return;
    }

    try {
      // Update the config with new data
      // We keep the theme in sync with root props
      const newConfig: LandingPageConfig = {
        ...initialConfig,
        theme: newData.root.props?.theme || initialConfig.theme,
        content: newData as unknown as LandingPageConfig["content"], // Store Puck Data directly
      };

      await offerApi.updateLandingPage(offerId, newConfig, token);
      toast.success("Landing Page guardada exitosamente");
    } catch (error) {
      console.error(error);
      toast.error("Error al guardar la landing page");
    }
  };

  return (
    <div id="puck-editor-wrapper" className="flex flex-col h-screen bg-white">
      <div className="flex-1 overflow-hidden relative">
        <Puck
          config={config}
          data={data}
          onPublish={handleSave}
          overrides={{
            header: ({ actions, children }) => (
              <div className="flex items-center justify-between px-4 py-3 border-b bg-white">
                <div className="flex items-center gap-4">
                  <Link href={`/${tenantId}/offer-studio/offer/${offerId}`}>
                    <Button variant="ghost" size="sm">
                      <ArrowLeft className="w-4 h-4 mr-2" /> Salir del modo Editor
                    </Button>
                  </Link>
                  <h1 className="font-semibold text-lg text-slate-900">Visionary Canvas</h1>
                </div>
                <div className="flex gap-2">
                  <AiRemixButton offerId={offerId} />
                  {children}
                </div>
              </div>
            ),
          }}
        />
      </div>

      {/* Custom Styles for Puck UI override - SCOPED TO WRAPPER */}
      <style jsx global>{`
        /* 
                   SCOPE: #puck-editor-wrapper
                   We force redefine CSS variables inside this wrapper to ensure Light Mode colors
                   are used for Puck, regardless of the system/app Dark Mode preference.
                */
        #puck-editor-wrapper {
          --background: 0 0% 100%;
          --foreground: 222.2 84% 4.9%;
          --card: 0 0% 100%;
          --card-foreground: 222.2 84% 4.9%;
          --popover: 0 0% 100%;
          --popover-foreground: 222.2 84% 4.9%;
          --primary: 222.2 47.4% 11.2%;
          --primary-foreground: 210 40% 98%;
          --secondary: 210 40% 96.1%;
          --secondary-foreground: 222.2 47.4% 11.2%;
          --muted: 210 40% 96.1%;
          --muted-foreground: 215.4 16.3% 46.9%;
          --accent: 210 40% 96.1%;
          --accent-foreground: 222.2 47.4% 11.2%;
          --destructive: 0 84.2% 60.2%;
          --destructive-foreground: 210 40% 98%;
          --border: 214.3 31.8% 91.4%;
          --input: 214.3 31.8% 91.4%;
          --ring: 222.2 84% 4.9%;
          --radius: 0.5rem;
        }

        /* Ensure all children inherit these colors */
        #puck-editor-wrapper * {
          border-color: hsl(var(--border));
        }
      `}</style>
    </div>
  );
}
