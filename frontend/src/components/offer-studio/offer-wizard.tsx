"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { CheckCircle2, Circle, ArrowRight, Save } from "lucide-react";
import { ObjectionEditor } from "./objection-editor";
import { AssetUploader } from "./asset-uploader";

export function OfferWizard() {
  const [step, setStep] = useState("avatar");
  
  // State for forms (Simplified for prototype)
  const [avatar, setAvatar] = useState({ icp: "", anti: "" });
  const [offer, setOffer] = useState({ name: "", promise: "", price: "" });
  
  const steps = [
    { id: "avatar", label: "1. Avatar Core" },
    { id: "offer", label: "2. The Offer" },
    { id: "objections", label: "3. Objections" },
    { id: "context", label: "4. Context" },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Stepper Navigation */}
      <div className="flex w-full items-center justify-between px-4 overflow-x-auto">
        {steps.map((s, idx) => (
          <div key={s.id} className="flex items-center gap-2 min-w-fit">
             <div className={`flex items-center justify-center w-8 h-8 rounded-full border transition-colors ${step === s.id ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
                {idx + 1}
             </div>
             <span className={`text-sm font-medium ${step === s.id ? "text-primary" : "text-muted-foreground"}`}>
               {s.label}
             </span>
             {idx < steps.length - 1 && <div className="h-[1px] w-12 bg-muted mx-2 hidden sm:block" />}
          </div>
        ))}
      </div>

      <Card className="min-h-[500px]">
        <CardHeader>
          <CardTitle>{steps.find(s => s.id === step)?.label}</CardTitle>
          <CardDescription>Configure los detalles para este paso.</CardDescription>
        </CardHeader>
        <CardContent>
           <Tabs value={step} onValueChange={setStep} className="w-full">
             
             {/* STEP 1: AVATAR */}
             <TabsContent value="avatar" className="space-y-4">
                <div className="space-y-2">
                  <Label>Descripción del Cliente Ideal (ICP)</Label>
                  <Textarea 
                    placeholder="Describe demografía, dolores y deseos profundos..." 
                    className="min-h-[150px]"
                    value={avatar.icp}
                    onChange={e => setAvatar({...avatar, icp: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Anti-Avatar (A quién NO vender)</Label>
                  <Textarea 
                    placeholder="Clientes sin presupuesto, quejumbrosos, competencia..." 
                    value={avatar.anti}
                    onChange={e => setAvatar({...avatar, anti: e.target.value})}
                  />
                </div>
                <div className="flex justify-end">
                   <Button onClick={() => setStep("offer")}>
                     Siguiente <ArrowRight className="ml-2 h-4 w-4" />
                   </Button>
                </div>
             </TabsContent>

             {/* STEP 2: OFFER */}
             <TabsContent value="offer" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                   <div className="space-y-2">
                     <Label>Nombre de la Oferta</Label>
                     <Input placeholder="High Ticket Mentorship" value={offer.name} onChange={e => setOffer({...offer, name: e.target.value})} />
                   </div>
                   <div className="space-y-2">
                     <Label>Precio (USD)</Label>
                     <Input type="number" placeholder="2000" value={offer.price} onChange={e => setOffer({...offer, price: e.target.value})} />
                   </div>
                </div>
                <div className="space-y-2">
                  <Label>Promesa de Transformación</Label>
                  <Textarea 
                    placeholder="Te ayudamos a lograr X en Y tiempo sin Z..." 
                    className="min-h-[100px]"
                    value={offer.promise}
                    onChange={e => setOffer({...offer, promise: e.target.value})}
                  />
                </div>
                <div className="flex justify-between">
                   <Button variant="outline" onClick={() => setStep("avatar")}>Anterior</Button>
                   <Button onClick={() => setStep("objections")}>
                     Siguiente <ArrowRight className="ml-2 h-4 w-4" />
                   </Button>
                </div>
             </TabsContent>

             {/* STEP 3: OBJECTIONS */}
             <TabsContent value="objections">
                <ObjectionEditor />
                 <div className="flex justify-between mt-4">
                   <Button variant="outline" onClick={() => setStep("offer")}>Anterior</Button>
                   <Button onClick={() => setStep("context")}>
                     Siguiente <ArrowRight className="ml-2 h-4 w-4" />
                   </Button>
                </div>
             </TabsContent>

             {/* STEP 4: CONTEXT */}
             <TabsContent value="context">
                <AssetUploader />
                 <div className="flex justify-between mt-4">
                   <Button variant="outline" onClick={() => setStep("objections")}>Anterior</Button>
                   <Button onClick={() => alert("Guardado! (Mock)")}>
                     <Save className="mr-2 h-4 w-4" /> Finalizar y Guardar
                   </Button>
                </div>
             </TabsContent>

           </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
