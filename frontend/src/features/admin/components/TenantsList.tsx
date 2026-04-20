"use client";
import { useAuth } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { adminApi } from "@/lib/api/admin";

import type { Tenant } from "@/lib/api/admin";

/**
 *
 */
export function TenantsClient() {
  const { getToken } = useAuth();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadTenants = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const data = await adminApi.getTenants(token);
      setTenants(data);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    void loadTenants();
  }, [loadTenants]);

  const togglePermission = async (tenantId: string, currentValue: boolean) => {
    try {
      const token = await getToken();
      if (!token) return;

      // Optimistic update
      setTenants((prev) =>
        prev.map((t) => (t.id === tenantId ? { ...t, can_use_platform_keys: !currentValue } : t)),
      );

      await adminApi.updateTenantPermissions(token, tenantId, !currentValue);

      toast.success("Permisos actualizados");
    } catch (error) {
      console.error(error);
      toast.error("Error al actualizar");
      void loadTenants(); // Revert
    }
  };

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Gestión de Clientes (Tenants)</h1>
      <Card>
        <CardHeader>
          <CardTitle>Listado de Clientes</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="animate-spin" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Slug</TableHead>
                  <TableHead>Configuración AI</TableHead>
                  <TableHead>Permiso Platform Keys</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tenants.map((tenant) => (
                  <TableRow key={tenant.id}>
                    <TableCell className="font-medium">{tenant.name}</TableCell>
                    <TableCell>{tenant.slug}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        {tenant.openai_api_key_set ? (
                          <Badge variant="default" className="bg-green-600 hover:bg-green-700">
                            OpenAI
                          </Badge>
                        ) : (
                          <Badge variant="outline">OpenAI Missing</Badge>
                        )}
                        {tenant.gemini_api_key_set ? (
                          <Badge variant="default" className="bg-blue-600 hover:bg-blue-700">
                            Gemini
                          </Badge>
                        ) : (
                          <Badge variant="outline">Gemini Missing</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Switch
                          checked={tenant.can_use_platform_keys}
                          onCheckedChange={() =>
                            togglePermission(tenant.id, tenant.can_use_platform_keys)
                          }
                        />
                        <span className="text-sm text-muted-foreground">
                          {tenant.can_use_platform_keys ? "Permitido" : "Denegado"}
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
