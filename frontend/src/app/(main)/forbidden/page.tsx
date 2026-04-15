"use client";

import { useClerk } from "@clerk/nextjs";
import { ShieldAlert, LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";

export default function ForbiddenPage() {
  const { signOut } = useClerk();

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50 p-4">
      <Card className="w-full max-w-md shadow-lg border-red-100">
        <CardHeader className="text-center">
          <div className="mx-auto bg-red-100 p-3 rounded-full w-fit mb-4">
            <ShieldAlert className="h-8 w-8 text-red-600" />
          </div>
          <CardTitle className="text-2xl text-red-700">Acceso Denegado</CardTitle>
          <CardDescription>
            No tienes los permisos necesarios para ver este recurso.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center text-slate-600">
          <p>No tiene los permisos suficientes para acceder a las funciones.</p>
          <p className="mt-4">
            Por favor contáctese con el administrador de su organización o, si quiere adquirir una
            suscripción comuníquese a:
          </p>
          <p className="mt-2 font-medium text-primary">hola@alpacapurpura.lat</p>
        </CardContent>
        <CardFooter className="flex justify-center">
          <Button variant="outline" className="gap-2" onClick={() => signOut({ redirectUrl: "/" })}>
            <LogOut className="h-4 w-4" />
            Intentar con otra cuenta
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
