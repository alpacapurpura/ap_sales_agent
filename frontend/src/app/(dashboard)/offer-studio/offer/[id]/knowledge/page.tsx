"use client";

import { use } from "react";
import { OfferEditorLayout } from "@/components/offer-studio/layout/offer-editor-layout";
import { AssetUploader } from "@/components/offer-studio/asset-uploader";

export default function KnowledgePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <OfferEditorLayout offerId={id}>
       <div className="space-y-6 max-w-4xl">
          <h1 className="text-2xl font-bold">Base de Conocimiento</h1>
          <p className="text-muted-foreground">
            Sube webinars, VSLs o documentos PDF que expliquen esta oferta.
          </p>
          <AssetUploader />
       </div>
    </OfferEditorLayout>
  );
}
