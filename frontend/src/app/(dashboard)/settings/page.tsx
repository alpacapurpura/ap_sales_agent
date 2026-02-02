"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AIKeysForm } from "@/components/settings/ai-keys-form"
import { ProfileView } from "@/components/settings/profile-view"
import { WebhookView } from "@/components/settings/webhook-view"
import { GeneralSettingsForm } from "@/components/settings/general-settings-form"
import { Key, Settings as SettingsIcon, User, Webhook } from "lucide-react"
import { useSearchParams, useRouter } from "next/navigation"
import { useEffect, useState, Suspense } from "react"

function SettingsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const tabParam = searchParams.get("tab")
  
  const [activeTab, setActiveTab] = useState(tabParam || "ai-keys")

  useEffect(() => {
    if (tabParam) {
      setActiveTab(tabParam)
    }
  }, [tabParam])

  const handleTabChange = (value: string) => {
    setActiveTab(value)
    router.push(`/settings?tab=${value}`)
  }

  return (
    <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <Tabs value={activeTab} onValueChange={handleTabChange} className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12">
            <aside className="-mx-4 lg:w-1/5">
                <TabsList className="flex flex-col h-auto items-start justify-start bg-transparent p-0 space-y-1">
                    <TabsTrigger 
                        value="general" 
                        className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                        <SettingsIcon className="mr-2 h-4 w-4" />
                        General
                    </TabsTrigger>
                    <TabsTrigger 
                        value="profile" 
                        className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                        <User className="mr-2 h-4 w-4" />
                        Perfil
                    </TabsTrigger>
                    <TabsTrigger 
                        value="ai-keys" 
                        className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                        <Key className="mr-2 h-4 w-4" />
                        LLM API Key&apos;s
                    </TabsTrigger>
                </TabsList>
            </aside>
            <div className="flex-1 lg:max-w-2xl">
                <TabsContent value="ai-keys" className="space-y-6 mt-0">
                    <AIKeysForm />
                </TabsContent>
                <TabsContent value="profile" className="space-y-6 mt-0">
                    <ProfileView />
                </TabsContent>
                <TabsContent value="general">
                    <div>General Settings (Próximamente)</div>
                </TabsContent>
            </div>
        </Tabs>
      </div>
  )
}

export default function SettingsPage() {
  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Configuración</h2>
        <p className="text-muted-foreground">
          Administra la configuración de tu cuenta y preferencias del sistema.
        </p>
      </div>
      <Suspense fallback={<div>Cargando configuración...</div>}>
        <SettingsContent />
      </Suspense>
    </div>
  )
}
