"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@clerk/nextjs"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Loader2, UserPlus, Users } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { settingsApi, TeamMember } from "@/lib/api/settings"
import { toast } from "sonner"

const formSchema = z.object({
  full_name: z.string().min(2, "El nombre debe tener al menos 2 caracteres"),
  email: z.string().email("Email inválido"),
  password: z.string().min(8, "La contraseña debe tener al menos 8 caracteres"),
})

export function TeamView() {
  const { getToken } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [team, setTeam] = useState<TeamMember[]>([])
  const [open, setOpen] = useState(false)

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
    },
  })

  const loadTeam = async () => {
      setIsLoading(true)
      try {
        const token = await getToken()
        if (!token) return
        const data = await settingsApi.getTeam(token)
        setTeam(data)
      } catch (error) {
        console.error(error)
        toast.error("Error al cargar el equipo.")
      } finally {
        setIsLoading(false)
      }
  }

  useEffect(() => {
    loadTeam()
  }, [getToken])

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsCreating(true)
    try {
      const token = await getToken()
      if (!token) return
      
      await settingsApi.createTeamMember(values, token)
      toast.success("Usuario creado correctamente")
      setOpen(false)
      form.reset()
      loadTeam()
    } catch (error: any) {
      console.error(error)
      toast.error(error.message || "Error al crear usuario")
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
            <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Gestión del Equipo
            </CardTitle>
            <CardDescription>
            Administra los usuarios que tienen acceso a esta Organización (Máximo 3).
            </CardDescription>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button disabled={team.length >= 3}>
                    <UserPlus className="mr-2 h-4 w-4" />
                    Agregar Miembro
                </Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Agregar Nuevo Miembro</DialogTitle>
                    <DialogDescription>
                        Crea un nuevo usuario para tu equipo. Este usuario tendrá acceso al dashboard.
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                            control={form.control}
                            name="full_name"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Nombre Completo</FormLabel>
                                    <FormControl>
                                        <Input placeholder="Juan Pérez" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="email"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Email</FormLabel>
                                    <FormControl>
                                        <Input placeholder="juan@empresa.com" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="password"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Contraseña</FormLabel>
                                    <FormControl>
                                        <Input type="password" placeholder="********" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <div className="flex justify-end">
                            <Button type="submit" disabled={isCreating}>
                                {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Crear Usuario
                            </Button>
                        </div>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        {isLoading ? (
            <div className="flex justify-center p-4">
                <Loader2 className="h-6 w-6 animate-spin" />
            </div>
        ) : (
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Nombre</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Rol</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Creado</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {team.map((member) => (
                        <TableRow key={member.id}>
                            <TableCell className="font-medium">{member.full_name}</TableCell>
                            <TableCell>{member.email}</TableCell>
                            <TableCell className="capitalize">{member.role}</TableCell>
                            <TableCell>
                                {member.is_active ? (
                                    <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-800">
                                        Activo
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-800">
                                        Inactivo
                                    </span>
                                )}
                            </TableCell>
                            <TableCell>{new Date(member.created_at).toLocaleDateString()}</TableCell>
                        </TableRow>
                    ))}
                    {team.length === 0 && (
                        <TableRow>
                            <TableCell colSpan={5} className="text-center text-muted-foreground h-24">
                                No hay miembros en el equipo.
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        )}
        <div className="mt-4 text-xs text-muted-foreground">
            {team.length} / 3 usuarios utilizados.
        </div>
      </CardContent>
    </Card>
  )
}
