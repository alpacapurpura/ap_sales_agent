"use client";

import { use } from "react";
import { OfferEditorLayout } from "@/components/offer-studio/layout/offer-editor-layout";
import { ObjectionEditor } from "@/components/offer-studio/objection-editor";

export default function ObjectionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <OfferEditorLayout offerId={id}>
       <div className="space-y-6 max-w-4xl">
          <h1 className="text-2xl font-bold">Matriz de Objeciones</h1>
          <p className="text-muted-foreground">
            Entrena al agente para manejar las dudas específicas de esta oferta.
          </p>
          <ObjectionEditor />
       </div>
    </OfferEditorLayout>
  );
}
