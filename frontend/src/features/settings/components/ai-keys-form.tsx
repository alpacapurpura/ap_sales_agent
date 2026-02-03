"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@clerk/nextjs"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Loader2, Key, AlertTriangle, CheckCircle } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { settingsApi, AISettings } from "@/lib/api/settings"
import { toast } from "sonner"

const formSchema = z.object({
  openai_api_key: z.string().optional(),
  gemini_api_key: z.string().optional(),
})

export function AIKeysForm() {
  const { getToken } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [settings, setSettings] = useState<AISettings | null>(null)

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      openai_api_key: "",
      gemini_api_key: "",
    },
  })

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const token = await getToken()
        if (!token) return
        const data = await settingsApi.getAISettings(token)
        setSettings(data)
        // Only set values if they exist, otherwise keep empty string
        form.reset({
          openai_api_key: data.openai_api_key || "",
          gemini_api_key: data.gemini_api_key || "",
        })
      } catch (error) {
        console.error(error)
        toast.error("Error al cargar la configuración.")
      }
    }
    loadSettings()
  }, [getToken, form])

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsLoading(true)
    try {
      const token = await getToken()
      if (!token) return
      
      const updated = await settingsApi.updateAISettings(values, token)
      setSettings(updated)
      toast.success("Configuración actualizada", {
        description: "Tus API Keys se han guardado correctamente.",
      })
    } catch (error) {
      console.error(error)
      toast.error("Error al guardar", {
        description: "No se pudieron guardar los cambios.",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Determine status
  const hasUserKeys = settings?.openai_api_key || settings?.gemini_api_key
  const hasPermission = settings?.can_use_platform_keys
  const needsConfiguration = !hasUserKeys && !hasPermission

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Configuración de Modelos IA
        </CardTitle>
        <CardDescription>
          Ingresa tus propias API Keys para tener control total sobre el consumo y los límites.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* Status Alert */}
        {settings && (
            <>
                {needsConfiguration && (
                    <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Configuración Requerida</AlertTitle>
                        <AlertDescription>
                            No tienes permiso para usar las llaves de la plataforma. Debes ingresar tus propias API Keys para que el agente funcione.
                        </AlertDescription>
                    </Alert>
                )}
                
                {!needsConfiguration && !hasUserKeys && hasPermission && (
                    <Alert className="bg-blue-50 border-blue-200 text-blue-800">
                        <CheckCircle className="h-4 w-4 text-blue-600" />
                        <AlertTitle>Todo listo</AlertTitle>
                        <AlertDescription>
                            Estás usando las credenciales de la plataforma. Puedes ingresar las tuyas si prefieres.
                        </AlertDescription>
                    </Alert>
                )}

                {hasUserKeys && (
                    <Alert className="bg-green-50 border-green-200 text-green-800">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <AlertTitle>API Keys Personalizadas</AlertTitle>
                        <AlertDescription>
                            El sistema está utilizando tus credenciales personales.
                        </AlertDescription>
                    </Alert>
                )}
            </>
        )}

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="openai_api_key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>OpenAI API Key</FormLabel>
                  <FormControl>
                    <Input placeholder="sk-..." type="password" {...field} />
                  </FormControl>
                  <FormDescription>
                    Requerido para modelos GPT-4 y GPT-3.5.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="gemini_api_key"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Google Gemini API Key</FormLabel>
                  <FormControl>
                    <Input placeholder="AIza..." type="password" {...field} />
                  </FormControl>
                  <FormDescription>
                    Requerido para modelos Gemini Pro y Flash.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Guardar Cambios
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
