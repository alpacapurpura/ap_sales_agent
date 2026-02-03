"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { UploadCloud, FileText, Video, Trash2, Link as LinkIcon } from "lucide-react";
import { MarketingAsset } from "@/lib/api/offer";

export function AssetUploader() {
  const [assets, setAssets] = useState<MarketingAsset[]>([
     { id: "1", name: "Webinar_Masterclass_V1.pdf", type: "PDF", size: "2.4 MB" }
  ]);
  const [urlInput, setUrlInput] = useState("");

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setAssets([...assets, {
        id: crypto.randomUUID(),
        name: file.name,
        type: file.type.includes("pdf") ? "PDF" : "VIDEO",
        size: `${(file.size / 1024 / 1024).toFixed(1)} MB`
      }]);
    }
  };

  const addUrl = () => {
    if (urlInput) {
       setAssets([...assets, {
        id: crypto.randomUUID(),
        name: urlInput,
        type: "URL",
        url: urlInput
      }]);
      setUrlInput("");
    }
  };

  const removeAsset = (id: string) => {
    setAssets(assets.filter(a => a.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
         {/* Upload Area */}
         <Card className="border-2 border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-10 space-y-4">
               <div className="p-4 bg-muted rounded-full">
                 <UploadCloud className="h-8 w-8 text-muted-foreground" />
               </div>
               <div className="text-center space-y-1">
                 <h4 className="font-medium">Sube tus archivos de contexto</h4>
                 <p className="text-sm text-muted-foreground">PDF, TXT, MD (Max 10MB)</p>
               </div>
               <div className="relative">
                 <Button variant="outline">Seleccionar Archivo</Button>
                 <Input 
                   type="file" 
                   className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
                   onChange={handleFileUpload}
                   accept=".pdf,.txt,.md"
                 />
               </div>
            </CardContent>
         </Card>

         {/* URL Area */}
         <Card>
            <CardContent className="pt-6 space-y-4">
               <div className="space-y-2">
                 <Label>Agregar recurso externo (URL)</Label>
                 <div className="flex gap-2">
                   <Input 
                     placeholder="https://youtube.com/..." 
                     value={urlInput}
                     onChange={(e) => setUrlInput(e.target.value)}
                   />
                   <Button onClick={addUrl}>Agregar</Button>
                 </div>
                 <p className="text-xs text-muted-foreground">
                   Soportamos YouTube (transcripción automática) y artículos de blog.
                 </p>
               </div>
            </CardContent>
         </Card>
      </div>

      {/* Asset List */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-muted-foreground">Archivos Cargados ({assets.length})</h4>
        <div className="space-y-2">
          {assets.map((asset) => (
            <div key={asset.id} className="flex items-center justify-between p-3 border rounded-md bg-card">
               <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-md bg-muted flex items-center justify-center">
                     {asset.type === "PDF" && <FileText className="h-5 w-5 text-blue-500" />}
                     {asset.type === "VIDEO" && <Video className="h-5 w-5 text-red-500" />}
                     {asset.type === "URL" && <LinkIcon className="h-5 w-5 text-green-500" />}
                  </div>
                  <div>
                    <p className="text-sm font-medium truncate max-w-[200px] md:max-w-[400px]">{asset.name}</p>
                    <p className="text-xs text-muted-foreground">{asset.type} • {asset.size || "Enlace externo"}</p>
                  </div>
               </div>
               <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-destructive" onClick={() => removeAsset(asset.id)}>
                 <Trash2 className="h-4 w-4" />
               </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
