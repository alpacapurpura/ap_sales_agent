"use client";

import { useAuth } from "@clerk/nextjs";
import {
  Loader2,
  CheckCircle,
  Trash2,
  Facebook,
  Instagram,
  BarChart3,
  RefreshCw,
  Users,
  ImageIcon,
  Crosshair,
  Link,
  Info,
  AlertTriangle,
  MessageCircle,
  Phone,
  Star,
} from "lucide-react";
import Image from "next/image";
import { useParams } from "next/navigation";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { fetchMetaAssets, syncMetaAssets, toggleMetaAsset } from "@/features/connections/api/meta-assets-api";
import { connectionsApi } from "@/lib/api/connections";
import { cn } from "@/lib/utils";

import type { MetaStatusResponse } from "@/lib/api/connections";
import type { MetaAssetsResponse } from "@/features/connections/api/meta-assets-api";

// ─── Helpers ─────────────────────────────────────────────────────────────────

const AD_ACCOUNT_STATUS: Record<number, { label: string; color: string }> = {
  1: { label: "Activa", color: "text-green-600" },
  2: { label: "Desactivada", color: "text-gray-500" },
  3: { label: "Saldo pendiente", color: "text-yellow-600" },
  7: { label: "En revisión", color: "text-yellow-600" },
  9: { label: "Cerrada", color: "text-red-600" },
  101: { label: "Pendiente cierre", color: "text-red-500" },
  201: { label: "Sancionada", color: "text-red-700" },
};

function formatFanCount(n?: number) {
  if (n == null) return null;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return `${n}`;
}

// ─── Sub-components ───────────────────────────────────────────────────────────

interface AssetToggleRowProps {
  isActive: boolean;
  hasCredentials: boolean;
  isToggling: boolean;
  onToggle: (val: boolean) => void;
}

const AssetToggleRow = ({
  isActive,
  hasCredentials,
  isToggling,
  onToggle,
}: AssetToggleRowProps) => (
  <Switch checked={isActive} disabled={isToggling || !hasCredentials} onCheckedChange={onToggle} />
);

// ─── Not Connected Screen ─────────────────────────────────────────────────────

function NotConnectedScreen({
  isConfigured,
  isConnecting,
  onConnect,
}: {
  isConfigured: boolean;
  isConnecting: boolean;
  onConnect: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Facebook className="h-6 w-6 text-blue-600" />
          Conectar Meta Business Suite
        </CardTitle>
        <CardDescription>
          Vincula tu cuenta de Meta para gestionar Páginas de Facebook, Instagram Business y
          Anuncios.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert className="bg-blue-50 text-blue-900 border-blue-200 dark:bg-blue-950/30 dark:text-blue-200 dark:border-blue-800">
          <Facebook className="h-4 w-4" />
          <AlertTitle className="text-sm font-semibold">Un login, control total</AlertTitle>
          <AlertDescription className="text-xs mt-1">
            Conectas tu cuenta Business Manager una vez y luego activas o desactivas cada Página,
            cuenta de Instagram o cuenta publicitaria de forma individual.
          </AlertDescription>
        </Alert>
        {!isConfigured && (
          <Alert variant="destructive">
            <AlertTitle>Meta no configurado</AlertTitle>
            <AlertDescription>
              La plataforma no tiene credenciales de Meta configuradas. Contacta al administrador.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter>
        <Button
          onClick={onConnect}
          disabled={isConnecting || !isConfigured}
          className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700"
        >
          {isConnecting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Facebook className="mr-2 h-4 w-4" />
          )}
          Conectar con Facebook
        </Button>
      </CardFooter>
    </Card>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

// eslint-disable-next-line sonarjs/cognitive-complexity -- Irreducible: MetaView manages 5 asset categories (pages, IG, ads, pixels, WhatsApp), each with toggle/primary mutations, plus sync/disconnect flows. The handlers share getToken and the optimistic-update setAssets closure — splitting would require context or additional hooks.
export function MetaView() {
  const { getToken } = useAuth();
  const params = useParams();
  const tenantId = params?.tenantId as string | undefined;

  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<MetaStatusResponse | null>(null);
  const [assets, setAssets] = useState<MetaAssetsResponse | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncWarnings, setSyncWarnings] = useState<string[]>([]);
  const [togglingAsset, setTogglingAsset] = useState<string | null>(null);
  const [settingPrimary, setSettingPrimary] = useState<string | null>(null);

  const handleSetPrimary = async (assetType: string, assetId: string) => {
    const key = `${assetType}:${assetId}`;
    try {
      setSettingPrimary(key);
      const token = await getToken();
      if (!token) return;
      await connectionsApi.setMetaPrimaryAsset(assetType, assetId, token);
      toast.success("Activo primario actualizado para analytics");
      await fetchStatus();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error configurando activo primario");
    } finally {
      setSettingPrimary(null);
    }
  };

  const fetchStatus = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    const data = await connectionsApi.getMetaStatus(token);
    setStatus(data);
    return data;
  }, [getToken]);

  const fetchAssets = useCallback(async () => {
    const token = await getToken();
    if (!token) return;
    try {
      const data = await fetchMetaAssets(token);
      setAssets(data);
    } catch {
      // assets are optional — don't block the UI
    }
  }, [getToken]);

  const loadAll = useCallback(async () => {
    try {
      setLoading(true);
      const st = await fetchStatus();
      if (st?.is_connected) await fetchAssets();
    } catch (e) {
      toast.error("Error al cargar estado de Meta");
    } finally {
      setLoading(false);
    }
  }, [fetchStatus, fetchAssets]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  // ── Connect ──
  const handleConnect = async () => {
    try {
      setConnecting(true);
      const token = await getToken();
      if (!token) return;
      const redirectUri = `${window.location.origin}/connections/meta/callback`;
      const { url } = await connectionsApi.getMetaAuthUrl(token, redirectUri);
      if (tenantId) sessionStorage.setItem("meta_oauth_tenant_id", tenantId);
      window.location.href = url;
    } catch {
      toast.error("No se pudo iniciar la conexión con Meta");
      setConnecting(false);
    }
  };

  // ── Sync assets from Meta API ──
  const handleSync = async () => {
    try {
      setSyncing(true);
      const token = await getToken();
      if (!token) return;
      const data = await syncMetaAssets(token);
      setAssets(data);
      setSyncWarnings(data.warnings ?? []);
      const total =
        data.pages.length +
        data.instagram_accounts.length +
        data.ads_accounts.length +
        data.pixels.length;
      toast.success(`Activos sincronizados: ${total} encontrado${total !== 1 ? "s" : ""}`);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al sincronizar activos de Meta");
    } finally {
      setSyncing(false);
    }
  };

  // ── Toggle asset ──
  const handleToggle = async (channelType: string, assetId: string, isActive: boolean) => {
    const key = `${channelType}:${assetId}`;
    try {
      setTogglingAsset(key);
      const token = await getToken();
      if (!token) return;
      await toggleMetaAsset(token, channelType, assetId, isActive);
      // Optimistic update
      setAssets((prev) => {
        if (!prev) return prev;
        const update = <T extends { is_active: boolean }>(
          arr: T[],
          idFn: (item: T) => string,
        ): T[] =>
          arr.map((item) => (idFn(item) === assetId ? { ...item, is_active: isActive } : item));
        return {
          ...prev,
          pages: update(prev.pages, (p) => p.page_id),
          instagram_accounts: update(prev.instagram_accounts, (ig) => ig.ig_account_id),
          ads_accounts: update(prev.ads_accounts, (ad) => ad.ad_account_id),
          pixels: update(prev.pixels, (px) => px.pixel_id),
          whatsapp_accounts: update(prev.whatsapp_accounts, (wa) => wa.waba_id),
        };
      });
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error actualizando activo");
      await fetchAssets();
    } finally {
      setTogglingAsset(null);
    }
  };

  // ── Disconnect ──
  const handleDisconnect = async () => {
    try {
      setDisconnecting(true);
      const token = await getToken();
      if (!token) return;
      await connectionsApi.disconnectMeta(token);
      toast.success("Meta desconectado");
      setStatus((prev) => ({ is_connected: false, is_configured: prev?.is_configured }));
      setAssets(null);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al desconectar");
    } finally {
      setDisconnecting(false);
    }
  };

  // ── Loading ──
  if (loading) {
    return (
      <Card>
        <CardContent className="py-10 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  // ── Not connected ──
  if (!status?.is_connected) {
    return (
      <NotConnectedScreen
        isConfigured={status?.is_configured ?? false}
        isConnecting={connecting}
        onConnect={handleConnect}
      />
    );
  }

  // ── Connected ──
  return (
    <div className="space-y-4">
      {/* Header card */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Meta Business Suite Conectado
              </CardTitle>
              <CardDescription className="mt-1">
                {status.name ? (
                  <>
                    Cuenta: <span className="font-medium text-foreground">{status.name}</span>
                  </>
                ) : (
                  "Tu cuenta de Meta está activa."
                )}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button variant="outline" size="sm" onClick={handleSync} disabled={syncing}>
                {syncing ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-1.5 h-4 w-4" />
                )}
                Sincronizar activos
              </Button>
              <Button variant="outline" size="sm" onClick={handleConnect} disabled={connecting}>
                {connecting ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : (
                  <Link className="mr-1.5 h-4 w-4" />
                )}
                Reconectar permisos
              </Button>
              <Dialog>
                <DialogTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="mr-1.5 h-4 w-4" />
                    Desvincular
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>¿Desvincular Meta?</DialogTitle>
                    <DialogDescription>
                      Se desactivarán todas las Páginas, cuentas de Instagram y cuentas
                      publicitarias conectadas.
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <Button variant="outline">Cancelar</Button>
                    <Button
                      variant="destructive"
                      onClick={handleDisconnect}
                      disabled={disconnecting}
                    >
                      {disconnecting ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        "Sí, desvincular"
                      )}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>

        {!assets && (
          <>
            <Separator />
            <CardContent className="pt-5">
              <div className="flex flex-col items-center justify-center py-8 text-center gap-3 text-muted-foreground">
                <RefreshCw className="h-8 w-8 opacity-30" />
                <p className="text-sm">
                  Aún no se han sincronizado los activos de tu Business Manager.
                </p>
                <Button onClick={handleSync} disabled={syncing} variant="outline" size="sm">
                  {syncing ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-2 h-4 w-4" />
                  )}
                  Sincronizar ahora
                </Button>
              </div>
            </CardContent>
          </>
        )}
      </Card>

      {/* Sync warnings from backend diagnostics */}
      {syncWarnings.length > 0 && (
        <Alert className="bg-yellow-50 text-yellow-900 border-yellow-300 dark:bg-yellow-950/30 dark:text-yellow-200 dark:border-yellow-800">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle className="text-sm font-semibold">Advertencias de sincronización</AlertTitle>
          <AlertDescription className="text-xs mt-1 space-y-1">
            {syncWarnings.map((w, i) => (
              <p key={i}>{w}</p>
            ))}
          </AlertDescription>
        </Alert>
      )}

      {/* Informative alert when at least one category is empty */}
      {assets &&
        (assets.pages.length === 0 ||
          assets.instagram_accounts.length === 0 ||
          assets.ads_accounts.length === 0 ||
          assets.pixels.length === 0) && (
          <Alert className="bg-blue-50 text-blue-900 border-blue-200 dark:bg-blue-950/30 dark:text-blue-200 dark:border-blue-800">
            <Info className="h-4 w-4" />
            <AlertTitle className="text-sm font-semibold">¿Falta algo?</AlertTitle>
            <AlertDescription className="text-xs mt-1">
              Si no ves todas tus páginas, cuentas de Instagram o publicitarias, puede que necesites
              reconectar para actualizar los permisos otorgados a Nicolify.
              <Button
                variant="link"
                size="sm"
                className="h-auto p-0 ml-1 text-xs text-blue-700 dark:text-blue-300"
                onClick={handleConnect}
                disabled={connecting}
              >
                {connecting ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : null}
                Reconectar permisos
              </Button>
            </AlertDescription>
          </Alert>
        )}

      {/* Asset sections — always show all 4 categories when assets have been fetched */}
      {assets && (
        <>
          {/* Facebook Pages */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Facebook className="h-4 w-4 text-blue-600" />
                Páginas de Facebook
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              {assets.pages.length > 0 ? (
                assets.pages.map((page) => {
                  const key = `facebook_page:${page.page_id}`;
                  const isToggling = togglingAsset === key;
                  return (
                    <div
                      key={page.page_id}
                      className={cn(
                        "flex items-center gap-3 rounded-lg border p-3 transition-colors",
                        page.is_active ? "border-border bg-card" : "border-border/50 bg-muted/30",
                      )}
                    >
                      {/* Avatar */}
                      <div className="h-10 w-10 shrink-0 rounded-lg overflow-hidden border bg-muted flex items-center justify-center">
                        {page.picture_url ? (
                          <Image
                            src={page.picture_url}
                            alt={page.page_name}
                            width={40}
                            height={40}
                            className="h-full w-full object-cover"
                            unoptimized
                          />
                        ) : (
                          <ImageIcon className="h-5 w-5 text-muted-foreground" />
                        )}
                      </div>
                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-medium text-sm truncate">{page.page_name}</span>
                          {page.is_active && (
                            <Badge
                              variant="secondary"
                              className="text-[10px] px-1.5 py-0 text-green-700 bg-green-100 border-green-200"
                            >
                              Activa
                            </Badge>
                          )}
                          {page.is_active && status?.config?.tracked_page_id === page.page_id && (
                            <Badge
                              variant="secondary"
                              className="text-[10px] px-1.5 py-0 text-amber-700 bg-amber-100 border-amber-200"
                            >
                              <Star className="h-2.5 w-2.5 mr-0.5 fill-current" /> Analytics
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground flex-wrap">
                          {page.category && <span>{page.category}</span>}
                          {page.fan_count != null && (
                            <span className="flex items-center gap-0.5">
                              <Users className="h-3 w-3" />
                              {formatFanCount(page.fan_count)}
                            </span>
                          )}
                          {page.instagram_username && (
                            <span className="flex items-center gap-0.5 text-pink-500">
                              <Instagram className="h-3 w-3" />@{page.instagram_username}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {page.is_active &&
                          assets.pages.length > 1 &&
                          status?.config?.tracked_page_id !== page.page_id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-[10px] h-7 px-2"
                              disabled={settingPrimary === `facebook_page:${page.page_id}`}
                              onClick={() => handleSetPrimary("facebook_page", page.page_id)}
                            >
                              {settingPrimary === `facebook_page:${page.page_id}` ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <>
                                  <Star className="h-3 w-3 mr-1" /> Usar para Analytics
                                </>
                              )}
                            </Button>
                          )}
                        <AssetToggleRow
                          isActive={page.is_active}
                          hasCredentials={page.has_credentials}
                          isToggling={isToggling}
                          onToggle={(val) => handleToggle("facebook_page", page.page_id, val)}
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="flex flex-col items-center py-4 text-center gap-2">
                  <p className="text-sm text-muted-foreground">
                    No se encontraron Páginas. Puede que no hayas seleccionado tus páginas al
                    conectar Meta.
                  </p>
                  <Button variant="outline" size="sm" onClick={handleConnect} disabled={connecting}>
                    {connecting ? (
                      <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                    ) : (
                      <Link className="mr-1.5 h-4 w-4" />
                    )}
                    Reconectar permisos
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Instagram Accounts */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Instagram className="h-4 w-4 text-pink-500" />
                Cuentas de Instagram Business
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              {assets.instagram_accounts.length > 0 ? (
                assets.instagram_accounts.map((ig) => {
                  const key = `instagram_account:${ig.ig_account_id}`;
                  const isToggling = togglingAsset === key;
                  return (
                    <div
                      key={ig.ig_account_id}
                      className={cn(
                        "flex items-center gap-3 rounded-lg border p-3 transition-colors",
                        ig.is_active ? "border-border bg-card" : "border-border/50 bg-muted/30",
                      )}
                    >
                      <div className="h-10 w-10 shrink-0 rounded-full overflow-hidden border bg-muted flex items-center justify-center">
                        {ig.profile_picture_url ? (
                          <Image
                            src={ig.profile_picture_url}
                            alt={ig.ig_username}
                            width={40}
                            height={40}
                            className="h-full w-full object-cover"
                            unoptimized
                          />
                        ) : (
                          <Instagram className="h-5 w-5 text-pink-400" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-medium text-sm">@{ig.ig_username}</span>
                          {ig.is_active && (
                            <Badge
                              variant="secondary"
                              className="text-[10px] px-1.5 py-0 text-green-700 bg-green-100 border-green-200"
                            >
                              Activa
                            </Badge>
                          )}
                          {ig.is_active && status?.config?.tracked_ig_id === ig.ig_account_id && (
                            <Badge
                              variant="secondary"
                              className="text-[10px] px-1.5 py-0 text-amber-700 bg-amber-100 border-amber-200"
                            >
                              <Star className="h-2.5 w-2.5 mr-0.5 fill-current" /> Analytics
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                          {ig.follower_count != null && (
                            <span className="flex items-center gap-0.5">
                              <Users className="h-3 w-3" />
                              {formatFanCount(ig.follower_count)} seguidores
                            </span>
                          )}
                          {ig.linked_page_name && (
                            <span className="flex items-center gap-0.5">
                              <Facebook className="h-3 w-3 text-blue-500" />
                              {ig.linked_page_name}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {ig.is_active &&
                          assets.instagram_accounts.length > 1 &&
                          status?.config?.tracked_ig_id !== ig.ig_account_id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-[10px] h-7 px-2"
                              disabled={settingPrimary === `instagram_account:${ig.ig_account_id}`}
                              onClick={() =>
                                handleSetPrimary("instagram_account", ig.ig_account_id)
                              }
                            >
                              {settingPrimary === `instagram_account:${ig.ig_account_id}` ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <>
                                  <Star className="h-3 w-3 mr-1" /> Usar para Analytics
                                </>
                              )}
                            </Button>
                          )}
                        <AssetToggleRow
                          isActive={ig.is_active}
                          hasCredentials={ig.has_credentials}
                          isToggling={isToggling}
                          onToggle={(val) =>
                            handleToggle("instagram_account", ig.ig_account_id, val)
                          }
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="flex flex-col items-center py-4 text-center gap-2">
                  <p className="text-sm text-muted-foreground">
                    No se encontraron cuentas de Instagram Business. Esto suele pasar cuando no
                    seleccionaste la Página vinculada a tu cuenta de IG al conectar. Reconecta para
                    elegir las páginas correctas.
                  </p>
                  <Button variant="outline" size="sm" onClick={handleConnect} disabled={connecting}>
                    {connecting ? (
                      <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                    ) : (
                      <Link className="mr-1.5 h-4 w-4" />
                    )}
                    Reconectar permisos
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Ads Accounts */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-orange-500" />
                Cuentas Publicitarias
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              {assets.ads_accounts.length > 0 ? (
                assets.ads_accounts.map((ad) => {
                  const key = `meta_ads_account:${ad.ad_account_id}`;
                  const isToggling = togglingAsset === key;
                  const statusInfo =
                    ad.account_status != null ? AD_ACCOUNT_STATUS[ad.account_status] : undefined;
                  return (
                    <div
                      key={ad.ad_account_id}
                      className={cn(
                        "flex items-center gap-3 rounded-lg border p-3 transition-colors",
                        ad.is_active ? "border-border bg-card" : "border-border/50 bg-muted/30",
                      )}
                    >
                      <div className="h-10 w-10 shrink-0 rounded-lg border bg-muted flex items-center justify-center">
                        <BarChart3 className="h-5 w-5 text-orange-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-medium text-sm truncate">{ad.ad_account_name}</span>
                          {ad.is_active && (
                            <Badge
                              variant="secondary"
                              className="text-[10px] px-1.5 py-0 text-green-700 bg-green-100 border-green-200"
                            >
                              Activa
                            </Badge>
                          )}
                          {ad.is_active &&
                            status?.config?.tracked_ad_account_id === ad.ad_account_id && (
                              <Badge
                                variant="secondary"
                                className="text-[10px] px-1.5 py-0 text-amber-700 bg-amber-100 border-amber-200"
                              >
                                <Star className="h-2.5 w-2.5 mr-0.5 fill-current" /> Analytics
                              </Badge>
                            )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                          {ad.currency && <span>{ad.currency}</span>}
                          {statusInfo && (
                            <span className={statusInfo.color}>{statusInfo.label}</span>
                          )}
                          <span className="text-muted-foreground/60">ID: {ad.ad_account_id}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {ad.is_active &&
                          assets.ads_accounts.length > 1 &&
                          status?.config?.tracked_ad_account_id !== ad.ad_account_id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-[10px] h-7 px-2"
                              disabled={settingPrimary === `meta_ads_account:${ad.ad_account_id}`}
                              onClick={() => handleSetPrimary("meta_ads_account", ad.ad_account_id)}
                            >
                              {settingPrimary === `meta_ads_account:${ad.ad_account_id}` ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <>
                                  <Star className="h-3 w-3 mr-1" /> Usar para Analytics
                                </>
                              )}
                            </Button>
                          )}
                        <AssetToggleRow
                          isActive={ad.is_active}
                          hasCredentials={ad.has_credentials}
                          isToggling={isToggling}
                          onToggle={(val) =>
                            handleToggle("meta_ads_account", ad.ad_account_id, val)
                          }
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="flex flex-col items-center py-4 text-center gap-2">
                  <p className="text-sm text-muted-foreground">
                    No se encontraron cuentas publicitarias. Si tienes una, reconecta para otorgar
                    acceso.
                  </p>
                  <Button variant="outline" size="sm" onClick={handleConnect} disabled={connecting}>
                    {connecting ? (
                      <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                    ) : (
                      <Link className="mr-1.5 h-4 w-4" />
                    )}
                    Reconectar permisos
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Meta Pixels */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Crosshair className="h-4 w-4 text-purple-500" />
                Meta Pixels
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              {assets.pixels.length > 0 ? (
                assets.pixels.map((px) => {
                  const key = `meta_pixel:${px.pixel_id}`;
                  const isToggling = togglingAsset === key;
                  return (
                    <div
                      key={px.pixel_id}
                      className={cn(
                        "flex items-center gap-3 rounded-lg border p-3 transition-colors",
                        px.is_active ? "border-border bg-card" : "border-border/50 bg-muted/30",
                      )}
                    >
                      <div className="h-10 w-10 shrink-0 rounded-lg border bg-muted flex items-center justify-center">
                        <Crosshair className="h-5 w-5 text-purple-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-medium text-sm truncate">{px.pixel_name}</span>
                          {px.is_active && (
                            <Badge
                              variant="secondary"
                              className="text-[10px] px-1.5 py-0 text-green-700 bg-green-100 border-green-200"
                            >
                              Activo
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                          <span className="text-muted-foreground/60">ID: {px.pixel_id}</span>
                          {px.linked_ad_account_id && (
                            <span className="flex items-center gap-0.5">
                              <BarChart3 className="h-3 w-3" />
                              Cuenta: {px.linked_ad_account_id}
                            </span>
                          )}
                        </div>
                      </div>
                      <AssetToggleRow
                        isActive={px.is_active}
                        hasCredentials={px.has_credentials}
                        isToggling={isToggling}
                        onToggle={(val) => handleToggle("meta_pixel", px.pixel_id, val)}
                      />
                    </div>
                  );
                })
              ) : (
                <div className="flex flex-col items-center py-4 text-center gap-2">
                  <p className="text-sm text-muted-foreground">
                    No se encontraron Meta Pixels. Si tienes uno configurado en tu cuenta
                    publicitaria, reconecta para otorgar acceso.
                  </p>
                  <Button variant="outline" size="sm" onClick={handleConnect} disabled={connecting}>
                    {connecting ? (
                      <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                    ) : (
                      <Link className="mr-1.5 h-4 w-4" />
                    )}
                    Reconectar permisos
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* WhatsApp Business Accounts */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <MessageCircle className="h-4 w-4 text-green-500" />
                WhatsApp Business
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              {assets.whatsapp_accounts.length > 0 ? (
                assets.whatsapp_accounts.map((wa) => {
                  const key = `whatsapp_business_account:${wa.waba_id}`;
                  const isToggling = togglingAsset === key;
                  return (
                    <div
                      key={wa.waba_id}
                      className={cn(
                        "flex items-center gap-3 rounded-lg border p-3 transition-colors",
                        wa.is_active ? "border-border bg-card" : "border-border/50 bg-muted/30",
                      )}
                    >
                      <div className="h-10 w-10 shrink-0 rounded-lg border bg-muted flex items-center justify-center">
                        <MessageCircle className="h-5 w-5 text-green-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="font-medium text-sm truncate">{wa.waba_name}</span>
                          {wa.is_active && (
                            <Badge
                              variant="secondary"
                              className="text-[10px] px-1.5 py-0 text-green-700 bg-green-100 border-green-200"
                            >
                              Activa
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground flex-wrap">
                          {wa.business_name && <span>{wa.business_name}</span>}
                          {wa.currency && <span>{wa.currency}</span>}
                          {wa.phone_numbers.length > 0 &&
                            wa.phone_numbers.map((ph) => (
                              <span
                                key={ph.phone_number_id}
                                className="flex items-center gap-0.5 text-green-600"
                              >
                                <Phone className="h-3 w-3" />
                                {ph.display_phone_number}
                                {ph.verified_name && (
                                  <span className="text-muted-foreground ml-0.5">
                                    ({ph.verified_name})
                                  </span>
                                )}
                              </span>
                            ))}
                        </div>
                      </div>
                      <AssetToggleRow
                        isActive={wa.is_active}
                        hasCredentials={wa.has_credentials}
                        isToggling={isToggling}
                        onToggle={(val) =>
                          handleToggle("whatsapp_business_account", wa.waba_id, val)
                        }
                      />
                    </div>
                  );
                })
              ) : (
                <div className="flex flex-col items-center py-4 text-center gap-2">
                  <p className="text-sm text-muted-foreground">
                    No se encontró ninguna cuenta de WhatsApp Business vinculada. Si usas WhatsApp
                    Business, reconecta tu cuenta de Meta para otorgar acceso.
                  </p>
                  <Button variant="outline" size="sm" onClick={handleConnect} disabled={connecting}>
                    {connecting ? (
                      <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                    ) : (
                      <Link className="mr-1.5 h-4 w-4" />
                    )}
                    Reconectar permisos
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
