"use client";

import { useClerk, useUser } from "@clerk/nextjs";
import { LogOut, Rocket, User, Mail } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/**
 *
 */
export default function OnboardingPage() {
  const { signOut } = useClerk();
  const { user } = useUser();

  // Redirect if user suddenly gets a tenant (e.g., admin assigns them)
  useEffect(() => {
    if (user?.publicMetadata?.tenant_id) {
      // Force hard reload to clear any cache and ensure middleware picks up the tenant
      window.location.href = "/";
    }
  }, [user]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-lg shadow-xl border-slate-200">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto bg-primary/10 p-4 rounded-full w-fit">
            <Rocket className="h-10 w-10 text-primary" />
          </div>
          <div className="space-y-2">
            <CardTitle className="text-3xl font-bold tracking-tight text-slate-900">
              ¡Bienvenido a Visionarias!
            </CardTitle>
            <CardDescription className="text-lg text-slate-600">
              Tu cuenta ha sido creada exitosamente.
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="bg-white p-4 rounded-lg border border-slate-100 shadow-sm space-y-3">
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <User className="h-4 w-4 text-primary/60" />
              <span className="font-medium">Nombre:</span>
              <span>{user?.fullName}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <Mail className="h-4 w-4 text-primary/60" />
              <span className="font-medium">Email:</span>
              <span>{user?.primaryEmailAddress?.emailAddress}</span>
            </div>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-md p-4 text-amber-800 text-sm">
            <p className="font-semibold mb-1">🛠️ Estado: Pendiente de Asignación</p>
            <p>
              Actualmente no tienes una organización asignada. Por razones de seguridad, solo el
              administrador del sistema puede asignar licencias y espacios de trabajo.
            </p>
          </div>

          <div className="text-center text-slate-600 text-sm">
            <p>Por favor, contacta a soporte para activar tu acceso:</p>
            <a
              href="mailto:hola@alpacapurpura.lat"
              className="text-primary font-medium hover:underline mt-1 block text-base"
            >
              hola@alpacapurpura.lat
            </a>
          </div>
        </CardContent>

        <CardFooter className="flex justify-center pt-2">
          <Button
            variant="outline"
            className="gap-2 border-slate-300 hover:bg-slate-100"
            onClick={() => signOut({ redirectUrl: "/" })}
          >
            <LogOut className="h-4 w-4" />
            Cerrar Sesión
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
