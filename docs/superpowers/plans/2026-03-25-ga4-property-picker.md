# GA4 Property Picker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After Google OAuth (both Workspace and Standalone flows), let users select which GA4 property to monitor so the ETL pipeline extracts real metrics.

**Architecture:** Add a `flatten_properties()` helper to the GA adapter, modify both OAuth callbacks to return flattened properties, add a `PUT /properties/select` endpoint, and create a frontend `PropertyPicker` component integrated into both connection views.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, Next.js 14, React 18, Tailwind CSS, Shadcn UI

**Spec:** `docs/superpowers/specs/2026-03-25-ga4-property-picker-design.md`

---

### Task 1: Add `flatten_properties()` to GA adapter

**Files:**
- Modify: `backend/src/modules/connections/infrastructure/channels/google_analytics.py:93-102`

- [ ] **Step 1: Add flatten helper method to GoogleAnalyticsAdapter**

```python
# Add after get_account_summaries() method (line 102)

def get_flat_properties(self) -> list[dict[str, str]]:
    """Fetch account summaries and return a flat list of properties.

    Returns:
        [{"property_id": "123", "display_name": "My Site", "account_name": "My Account"}, ...]
    """
    try:
        summaries = self.get_account_summaries()
    except Exception as e:
        logger.warning(f"Could not fetch account summaries: {e}")
        return []

    properties = []
    for account in summaries:
        account_name = account.get("displayName", "")
        for prop in account.get("propertySummaries", []):
            raw_property = prop.get("property", "")
            property_id = raw_property.split("/")[-1] if "/" in raw_property else raw_property
            properties.append({
                "property_id": property_id,
                "display_name": prop.get("displayName", property_id),
                "account_name": account_name,
            })
    return properties
```

- [ ] **Step 2: Verify import — no new imports needed**

The method uses only `self.get_account_summaries()` and the existing `logger`.

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/connections/infrastructure/channels/google_analytics.py
git commit -m "feat(connections): add flatten_properties helper to GA adapter"
```

---

### Task 2: Update DTOs for property picker

**Files:**
- Modify: `backend/src/modules/connections/api/dto/google_analytics.py`

- [ ] **Step 1: Replace DTO file with updated models**

```python
from pydantic import BaseModel
from typing import Optional, List


class GA4PropertySummary(BaseModel):
    property_id: str
    display_name: str
    account_name: str = ""


class PropertySelectRequest(BaseModel):
    property_id: str


class SelectedProperty(BaseModel):
    property_id: str
    display_name: str


class GoogleAnalyticsStatusResponse(BaseModel):
    is_connected: bool
    is_configured: bool = False
    selected_property: Optional[SelectedProperty] = None


class GoogleAnalyticsCallbackResponse(BaseModel):
    status: str
    properties: List[GA4PropertySummary] = []


class PropertySelectResponse(BaseModel):
    status: str
    property_id: str
    display_name: str
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/modules/connections/api/dto/google_analytics.py
git commit -m "feat(connections): add property picker DTOs"
```

---

### Task 3: Refactor standalone GA callback + add select endpoint

**Files:**
- Modify: `backend/src/modules/connections/api/google_analytics.py`

This is the largest backend change. Key modifications:
1. Callback returns properties (graceful fallback if Admin API fails)
2. New `PUT /properties/select` endpoint
3. Status returns `selected_property` from config
4. Properties endpoint returns flat list

- [ ] **Step 1: Replace the full router file**

```python
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import structlog

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import ChannelConnectionRepository
from src.modules.connections.infrastructure.models import ChannelConnectionModel
from src.modules.connections.infrastructure.channels.google_analytics import GoogleAnalyticsAdapter
from src.modules.connections.api.dto.google_analytics import (
    GoogleAnalyticsStatusResponse,
    GoogleAnalyticsCallbackResponse,
    GA4PropertySummary,
    PropertySelectRequest,
    PropertySelectResponse,
    SelectedProperty,
)

router = APIRouter(tags=["google_analytics"])
logger = structlog.get_logger()


class GoogleAnalyticsConfig(BaseModel):
    client_id: str
    client_secret: str


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


def _build_adapter(connection: ChannelConnectionModel, with_creds: bool = False) -> GoogleAnalyticsAdapter:
    """Build a GoogleAnalyticsAdapter from a connection model."""
    client_config = {
        "client_id": connection.credentials.get("client_id"),
        "client_secret": connection.credentials.get("client_secret"),
    }
    creds = dict(connection.credentials) if with_creds else None
    return GoogleAnalyticsAdapter(client_config=client_config, credentials_data=creds)


@router.put("/config")
async def save_config(
    config: GoogleAnalyticsConfig,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Save Google Analytics client configuration (client_id, client_secret)."""
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    creds_update = {"client_id": config.client_id, "client_secret": config.client_secret}

    if connection:
        existing_creds = dict(connection.credentials) if connection.credentials else {}
        existing_creds.update(creds_update)
        repo.update_credentials(connection, existing_creds)
    else:
        connection = ChannelConnectionModel(
            tenant_id=user.tenant_id,
            channel_type=ChannelType.GOOGLE_ANALYTICS.value,
            credentials=creds_update,
            config={},
            is_active=False,
        )
        repo.db.add(connection)
        repo.db.commit()

    return {"status": "config_saved"}


@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: Optional[str] = None,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if (
        not connection
        or not connection.credentials
        or "client_id" not in connection.credentials
        or "client_secret" not in connection.credentials
    ):
        raise HTTPException(
            status_code=400,
            detail="Configuracion de cliente no encontrada. Configure client_id y client_secret primero.",
        )

    adapter = _build_adapter(connection)
    url, state = adapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}


@router.post("/callback", response_model=GoogleAnalyticsCallbackResponse)
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: Optional[str] = Body(None, embed=True),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if (
        not connection
        or not connection.credentials
        or "client_id" not in connection.credentials
        or "client_secret" not in connection.credentials
    ):
        raise HTTPException(status_code=400, detail="Configuracion de cliente no encontrada.")

    # Exchange code for tokens
    try:
        adapter = _build_adapter(connection)
        token_data = await asyncio.to_thread(adapter.exchange_code, code, redirect_uri)
    except Exception as e:
        logger.error("google_analytics_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticacion con Google")

    # Save credentials FIRST (don't block on Admin API)
    full_creds = dict(connection.credentials)
    full_creds.update(token_data)
    connection.credentials = full_creds
    connection.is_active = True
    repo.db.commit()

    # Try to fetch properties (graceful fallback)
    properties: List[GA4PropertySummary] = []
    try:
        adapter = _build_adapter(connection, with_creds=True)
        flat = await asyncio.to_thread(adapter.get_flat_properties)
        properties = [GA4PropertySummary(**p) for p in flat]

        # Update config with account count
        repo.update_config(connection, {"account_count": len(flat)})
    except Exception as e:
        logger.warning("google_analytics_properties_fetch_failed", error=str(e), tenant_id=str(user.tenant_id))

    return GoogleAnalyticsCallbackResponse(status="connected", properties=properties)


@router.get("/status", response_model=GoogleAnalyticsStatusResponse)
async def get_status(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection:
        return GoogleAnalyticsStatusResponse(is_connected=False, is_configured=False)

    has_client_id = bool(connection.credentials and connection.credentials.get("client_id"))
    is_connected = bool(connection.is_active and connection.credentials and connection.credentials.get("refresh_token"))

    # Read selected property from config (fast, no API call)
    selected = None
    config = connection.config or {}
    if config.get("property_id"):
        selected = SelectedProperty(
            property_id=config["property_id"],
            display_name=config.get("property_display_name", config["property_id"]),
        )

    return GoogleAnalyticsStatusResponse(
        is_connected=is_connected,
        is_configured=has_client_id,
        selected_property=selected,
    )


@router.get("/properties", response_model=List[GA4PropertySummary])
async def get_properties(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")

    try:
        adapter = _build_adapter(connection, with_creds=True)
        flat = await asyncio.to_thread(adapter.get_flat_properties)
        return [GA4PropertySummary(**p) for p in flat]
    except Exception as e:
        logger.error("google_analytics_properties_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error al obtener propiedades de Google Analytics")


@router.put("/properties/select", response_model=PropertySelectResponse)
async def select_property(
    body: PropertySelectRequest,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")

    # Try to validate + get display_name from Admin API
    display_name = body.property_id
    try:
        adapter = _build_adapter(connection, with_creds=True)
        flat = await asyncio.to_thread(adapter.get_flat_properties)
        match = next((p for p in flat if p["property_id"] == body.property_id), None)
        if match:
            display_name = match["display_name"]
    except Exception as e:
        logger.warning("property_validation_skipped", error=str(e))
        # Allow saving anyway (manual input fallback)

    # Save property_id in credentials (for ETL provider)
    creds = dict(connection.credentials)
    creds["property_id"] = body.property_id
    repo.update_credentials(connection, creds)

    # Save display info in config (for UI, no decryption needed)
    repo.update_config(connection, {
        "property_id": body.property_id,
        "property_display_name": display_name,
    })

    logger.info("ga4_property_selected", tenant_id=str(user.tenant_id), property_id=body.property_id)

    return PropertySelectResponse(
        status="ok",
        property_id=body.property_id,
        display_name=display_name,
    )


@router.delete("/disconnect")
async def disconnect(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)
    if connection:
        repo.deactivate(connection)
    return {"status": "disconnected"}


@router.post("/test")
async def test_connection(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.GOOGLE_ANALYTICS)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")

    try:
        adapter = _build_adapter(connection, with_creds=True)
        summaries = await asyncio.to_thread(adapter.get_account_summaries)
        return {"status": "ok", "message": "Conexion exitosa", "data": summaries}
    except Exception as e:
        logger.error("google_analytics_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/modules/connections/api/google_analytics.py
git commit -m "feat(connections): refactor GA callback with property picker + select endpoint"
```

---

### Task 4: (No backend changes to Workspace callback)

The Workspace callback is left unchanged. The frontend (Task 8) fetches GA4 properties via the existing `GET /google-analytics/properties` endpoint after detecting the GA connection needs a property. This avoids blocking the Workspace OAuth flow with a synchronous Admin API call.

---

### Task 5: Update frontend API client

**Files:**
- Modify: `frontend/src/lib/api/connections.ts`

- [ ] **Step 1: Add new types after GoogleAnalyticsStatusResponse (line 56)**

```typescript
export interface GA4Property {
  property_id: string;
  display_name: string;
  account_name: string;
}

export interface SelectedProperty {
  property_id: string;
  display_name: string;
}

// Update the existing GoogleAnalyticsStatusResponse
export interface GoogleAnalyticsStatusResponse extends ChannelStatusResponse {
  account_summary?: any[];
  is_configured?: boolean;
  selected_property?: SelectedProperty | null;
}

export interface GoogleAnalyticsCallbackResponse {
  status: string;
  properties: GA4Property[];
}
```

- [ ] **Step 2: Add new API methods after `testGoogleAnalytics` (line 211)**

```typescript
  getGoogleAnalyticsProperties: async (token: string): Promise<GA4Property[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google-analytics/properties`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo propiedades de GA4");
    return res.json();
  },

  selectGoogleAnalyticsProperty: async (propertyId: string, token: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google-analytics/properties/select`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ property_id: propertyId }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error seleccionando propiedad");
    }
    return res.json();
  },
```

- [ ] **Step 3: Update `connectGoogleAnalytics` return type (line 175)**

Change the return type from `Promise<any>` to `Promise<GoogleAnalyticsCallbackResponse>`:

```typescript
  connectGoogleAnalytics: async (code: string, token: string, redirectUri?: string): Promise<GoogleAnalyticsCallbackResponse> => {
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/api/connections.ts
git commit -m "feat(connections): add GA4 property picker API methods"
```

---

### Task 6: Create PropertyPicker component

**Files:**
- Create: `frontend/src/features/connections/components/property-picker.tsx`

- [ ] **Step 1: Create the component**

```tsx
"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { connectionsApi, GA4Property } from "@/lib/api/connections";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle, Globe, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

interface PropertyPickerProps {
  /** Properties returned from OAuth callback or /properties endpoint */
  properties: GA4Property[];
  /** Called after successful property selection */
  onSelected: () => void;
  /** If true, shows as "change" mode instead of initial selection */
  isChangeMode?: boolean;
}

export function PropertyPicker({ properties, onSelected, isChangeMode = false }: PropertyPickerProps) {
  const { getToken } = useAuth();
  const [selectedId, setSelectedId] = useState<string>(
    properties.length === 1 ? properties[0].property_id : ""
  );
  const [manualId, setManualId] = useState("");
  const [showManual, setShowManual] = useState(properties.length === 0);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    const propertyId = showManual ? manualId.trim() : selectedId;
    if (!propertyId) {
      toast.error("Selecciona o ingresa una propiedad");
      return;
    }

    try {
      setSaving(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.selectGoogleAnalyticsProperty(propertyId, token);

      const name = properties.find((p) => p.property_id === propertyId)?.display_name || propertyId;
      toast.success(`Propiedad "${name}" configurada`);
      onSelected();
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error al guardar la propiedad");
    } finally {
      setSaving(false);
    }
  };

  // Auto-select if single property and not in change mode
  const autoSelected = properties.length === 1 && !isChangeMode;

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-sm font-medium">
          {isChangeMode ? "Cambiar propiedad GA4" : "Selecciona tu propiedad de Google Analytics"}
        </Label>
        <p className="text-xs text-muted-foreground">
          {properties.length > 0
            ? "Elige cuál sitio web quieres monitorear."
            : "No encontramos propiedades en tu cuenta. Puedes ingresar el ID manualmente."}
        </p>
      </div>

      {!showManual && properties.length > 0 ? (
        <div className="space-y-3">
          <Select value={selectedId} onValueChange={setSelectedId}>
            <SelectTrigger>
              <SelectValue placeholder="Selecciona una propiedad..." />
            </SelectTrigger>
            <SelectContent>
              {properties.map((prop) => (
                <SelectItem key={prop.property_id} value={prop.property_id}>
                  <div className="flex items-center gap-2">
                    <Globe className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <span>{prop.display_name}</span>
                    {prop.account_name && (
                      <span className="text-muted-foreground text-xs">— {prop.account_name}</span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {autoSelected && (
            <Alert className="bg-green-50 text-green-800 border-green-200 dark:bg-green-950/30 dark:text-green-200 dark:border-green-800">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                Detectamos tu propiedad automáticamente: <strong>{properties[0].display_name}</strong>
              </AlertDescription>
            </Alert>
          )}

          <button
            type="button"
            onClick={() => setShowManual(true)}
            className="text-xs text-muted-foreground underline hover:text-foreground"
          >
            Ingresar ID manualmente
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <Alert className="bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-200 dark:border-amber-800">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Ingresa el Property ID numérico de GA4. Lo encuentras en Google Analytics → Admin → Configuración de la propiedad.
            </AlertDescription>
          </Alert>

          <Input
            placeholder="Ej: 123456789"
            value={manualId}
            onChange={(e) => setManualId(e.target.value)}
          />

          {properties.length > 0 && (
            <button
              type="button"
              onClick={() => setShowManual(false)}
              className="text-xs text-muted-foreground underline hover:text-foreground"
            >
              Volver a la lista
            </button>
          )}
        </div>
      )}

      <Button onClick={handleSave} disabled={saving} className="w-full sm:w-auto">
        {saving ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <CheckCircle className="mr-2 h-4 w-4" />
        )}
        {isChangeMode ? "Cambiar propiedad" : "Confirmar"}
      </Button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/connections/components/property-picker.tsx
git commit -m "feat(connections): create PropertyPicker component"
```

---

### Task 7: Integrate PropertyPicker in google-analytics-view.tsx

**Files:**
- Modify: `frontend/src/features/connections/components/google-analytics-view.tsx`

- [ ] **Step 1: Rewrite the component to include property picker state**

Replace the full file content:

```tsx
"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { connectionsApi, GoogleAnalyticsStatusResponse, GA4Property } from "@/lib/api/connections";
import { useGoogleOAuthListener } from "@/features/connections/hooks/use-google-oauth-listener";
import { openOAuthPopup } from "@/features/connections/utils/open-oauth-popup";
import { PropertyPicker } from "@/features/connections/components/property-picker";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, CheckCircle, BarChart, Trash2, ExternalLink, Activity, Settings, Save, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function GoogleAnalyticsView() {
  const { getToken } = useAuth();

  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<GoogleAnalyticsStatusResponse | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  // Configuration State
  const [configMode, setConfigMode] = useState(false);
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [savingConfig, setSavingConfig] = useState(false);

  // Property Picker State
  const [properties, setProperties] = useState<GA4Property[]>([]);
  const [showPropertyPicker, setShowPropertyPicker] = useState(false);
  const [loadingProperties, setLoadingProperties] = useState(false);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getGoogleAnalyticsStatus(token);
      setStatus(data);

      if (data && !data.is_configured) {
          setConfigMode(true);
      }
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de Google Analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle OAuth Callback
  useGoogleOAuthListener({
    onSuccess: async (code) => {
      try {
        setConnecting(true);
        const token = await getToken();
        if (!token) return;

        toast.info("Finalizando conexión con Google Analytics...");
        const redirectUri = window.location.origin + "/connections";
        const result = await connectionsApi.connectGoogleAnalytics(code, token, redirectUri);

        toast.success("Google Analytics conectado");

        // Show property picker with returned properties
        if (result.properties && result.properties.length > 0) {
          setProperties(result.properties);
          setShowPropertyPicker(true);
        } else {
          // No properties returned — show picker with empty state (manual input)
          setProperties([]);
          setShowPropertyPicker(true);
        }

        await fetchStatus();
      } catch (error: any) {
        console.error(error);
        toast.error(error.message || "Error al conectar Google Analytics");
      } finally {
        setConnecting(false);
      }
    },
    onError: () => {
      toast.error("Error en autenticación de Google");
      setConnecting(false);
    },
  });

  const handleSaveConfig = async () => {
      if (!clientId || !clientSecret) {
          toast.error("Por favor completa todos los campos");
          return;
      }
      try {
          setSavingConfig(true);
          const token = await getToken();
          if (!token) return;
          await connectionsApi.configureGoogleAnalytics({ client_id: clientId, client_secret: clientSecret }, token);
          toast.success("Configuración guardada exitosamente");
          setConfigMode(false);
          await fetchStatus();
      } catch (error: any) {
          console.error(error);
          toast.error(error.message || "Error al guardar configuración");
      } finally {
          setSavingConfig(false);
      }
  };

  const handleConnect = async () => {
    try {
      setConnecting(true);
      const token = await getToken();
      if (!token) return;
      const redirectUri = window.location.origin + "/connections";
      const { url } = await connectionsApi.getGoogleAnalyticsAuthUrl(token, redirectUri);
      openOAuthPopup({ url, name: "GoogleAnalyticsAuth" });
      setTimeout(() => setConnecting(false), 60000);
    } catch (error: any) {
      console.error(error);
      toast.error("No se pudo iniciar la conexión. Verifica tu configuración.");
      setConnecting(false);
    }
  };

  const handleChangeProperty = async () => {
    try {
      setLoadingProperties(true);
      const token = await getToken();
      if (!token) return;
      const props = await connectionsApi.getGoogleAnalyticsProperties(token);
      setProperties(props);
      setShowPropertyPicker(true);
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error al obtener propiedades");
      // Show picker with empty properties (manual fallback)
      setProperties([]);
      setShowPropertyPicker(true);
    } finally {
      setLoadingProperties(false);
    }
  };

  const handlePropertySelected = () => {
    setShowPropertyPicker(false);
    fetchStatus();
  };

  const handleTest = async () => {
      try {
          setTesting(true);
          setTestResult(null);
          const token = await getToken();
          if (!token) return;
          const res = await connectionsApi.testGoogleAnalytics(token);
          setTestResult(res);
          toast.success("Prueba de conexión exitosa");
      } catch (error: any) {
          console.error(error);
          toast.error(error.message || "Error en la prueba");
          setTestResult({ status: "error", message: error.message });
      } finally {
          setTesting(false);
      }
  };

  const handleDisconnect = async () => {
    try {
      setDisconnecting(true);
      const token = await getToken();
      if (!token) return;
      await connectionsApi.disconnectGoogleAnalytics(token);
      toast.success("Google Analytics desconectado");
      setStatus((prev) => prev ? ({ ...prev, is_connected: false, selected_property: null }) : null);
      setTestResult(null);
      setShowPropertyPicker(false);
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error al desconectar");
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

  // ── Configuration Mode ──
  if (configMode) {
      return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Settings className="h-6 w-6 text-gray-500" />
                    Configuración de Google Analytics
                </CardTitle>
                <CardDescription>
                    Ingresa las credenciales de tu aplicación Google Cloud (OAuth 2.0 Client ID).
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <Alert className="bg-blue-50 text-blue-800 border-blue-200">
                    <ExternalLink className="h-4 w-4" />
                    <AlertTitle>Instrucciones</AlertTitle>
                    <AlertDescription>
                        1. Ve a Google Cloud Console.<br/>
                        2. Crea credenciales OAuth 2.0.<br/>
                        3. Añade <code>{typeof window !== 'undefined' ? window.location.origin : ''}</code> como Origen Autorizado.<br/>
                        4. Añade <code>{typeof window !== 'undefined' ? window.location.origin : ''}/connections</code> como URI de redirección.
                    </AlertDescription>
                </Alert>
                <div className="space-y-2">
                    <Label htmlFor="client_id">Client ID</Label>
                    <Input
                        id="client_id"
                        value={clientId}
                        onChange={(e) => setClientId(e.target.value)}
                        placeholder="apps.googleusercontent.com"
                    />
                </div>
                <div className="space-y-2">
                    <Label htmlFor="client_secret">Client Secret</Label>
                    <Input
                        id="client_secret"
                        type="password"
                        value={clientSecret}
                        onChange={(e) => setClientSecret(e.target.value)}
                        placeholder="Tu secreto de cliente"
                    />
                </div>
            </CardContent>
            <CardFooter className="flex justify-between">
                {status?.is_configured ? (
                    <Button variant="ghost" onClick={() => setConfigMode(false)}>Cancelar</Button>
                ) : (
                    <div></div>
                )}
                <Button onClick={handleSaveConfig} disabled={savingConfig}>
                    {savingConfig ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Guardar Configuración
                </Button>
            </CardFooter>
        </Card>
      );
  }

  // ── Not Connected ──
  if (!status?.is_connected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="h-6 w-6 text-orange-500" />
            Conectar Google Analytics
          </CardTitle>
          <CardDescription>
            Vincula tu cuenta de Google Analytics 4 para ver métricas de tráfico y conversión.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
            <Alert className="bg-blue-50 text-blue-800 border-blue-200">
                <ExternalLink className="h-4 w-4" />
                <AlertTitle>Google Analytics 4</AlertTitle>
                <AlertDescription>
                    Soportamos propiedades de Google Analytics 4 (GA4).
                </AlertDescription>
            </Alert>
            <div className="text-sm text-muted-foreground">
                <p>Al conectar, permitirás que el sistema:</p>
                <ul className="list-disc list-inside mt-2 space-y-1 ml-2">
                    <li>Leer propiedades y métricas de GA4.</li>
                    <li>Generar reportes de rendimiento.</li>
                </ul>
            </div>
        </CardContent>
        <CardFooter className="flex justify-between">
            <Button variant="outline" onClick={() => setConfigMode(true)}>
                <Settings className="mr-2 h-4 w-4" />
                Editar Config
            </Button>
            <Button onClick={handleConnect} disabled={connecting} className="bg-orange-600 hover:bg-orange-700">
                {connecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <BarChart className="mr-2 h-4 w-4" />}
                Conectar
            </Button>
        </CardFooter>
      </Card>
    );
  }

  // ── Connected but no property selected → Property Picker ──
  if (!status.selected_property || showPropertyPicker) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="h-6 w-6 text-orange-500" />
            {status.selected_property ? "Cambiar propiedad" : "Configura tu propiedad GA4"}
          </CardTitle>
          <CardDescription>
            {status.selected_property
              ? `Actualmente: ${status.selected_property.display_name}`
              : "Un último paso: selecciona qué sitio web quieres monitorear."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PropertyPicker
            properties={properties}
            onSelected={handlePropertySelected}
            isChangeMode={!!status.selected_property}
          />
        </CardContent>
      </Card>
    );
  }

  // ── Connected + property selected → Full status ──
  return (
    <div className="space-y-6">
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <BarChart className="h-6 w-6 text-orange-500" />
                        Analytics Conectado
                    </div>
                    <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                        <CheckCircle className="h-4 w-4" />
                        Activo
                    </div>
                </CardTitle>
                <CardDescription className="flex items-center gap-1.5">
                    Propiedad: <strong>{status.selected_property.display_name}</strong>
                    <button
                      type="button"
                      onClick={handleChangeProperty}
                      disabled={loadingProperties}
                      className="text-xs text-muted-foreground underline hover:text-foreground ml-1"
                    >
                      {loadingProperties ? "Cargando..." : "Cambiar"}
                    </button>
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                {testResult && (
                    <Alert variant={testResult.status === "ok" ? "default" : "destructive"} className={testResult.status === "ok" ? "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20" : ""}>
                        <Activity className="h-4 w-4" />
                        <AlertTitle>{testResult.status === "ok" ? "Conexión Estable" : "Error de Conexión"}</AlertTitle>
                        <AlertDescription>
                            {testResult.message}
                            {testResult.data && Array.isArray(testResult.data) && (
                                <div className="mt-2 text-xs bg-background/50 p-2 rounded overflow-x-auto text-foreground border border-border/50 max-h-40 overflow-y-auto">
                                    <p className="font-semibold mb-1">Cuentas encontradas: {testResult.data.length}</p>
                                    <ul className="list-disc pl-4">
                                        {testResult.data.map((acc: any, i: number) => (
                                            <li key={i}>{acc.account || acc.name} - {acc.displayName}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </AlertDescription>
                    </Alert>
                )}
            </CardContent>
            <CardFooter className="flex flex-col sm:flex-row gap-3 justify-between border-t pt-6">
                <div className="flex gap-2">
                    <Button variant="outline" onClick={handleTest} disabled={testing}>
                        {testing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Activity className="mr-2 h-4 w-4" />}
                        Probar
                    </Button>
                    <Button variant="outline" onClick={() => setConfigMode(true)}>
                        <Settings className="h-4 w-4" />
                    </Button>
                </div>

                <Dialog>
                    <DialogTrigger asChild>
                        <Button variant="destructive" disabled={disconnecting}>
                            <Trash2 className="mr-2 h-4 w-4" />
                            Desconectar
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>¿Desvincular Google Analytics?</DialogTitle>
                            <DialogDescription>
                                Dejarás de recibir métricas de esta cuenta.
                            </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                            <Button variant="outline">Cancelar</Button>
                            <Button variant="destructive" onClick={handleDisconnect} disabled={disconnecting}>
                                {disconnecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Sí, desconectar"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </CardFooter>
        </Card>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/connections/components/google-analytics-view.tsx
git commit -m "feat(connections): integrate PropertyPicker in GA view"
```

---

### Task 8: Integrate PropertyPicker in google-workspace-view.tsx

**Files:**
- Modify: `frontend/src/features/connections/components/google-workspace-view.tsx`

- [ ] **Step 1: Add imports at top (after existing imports)**

```tsx
import { PropertyPicker } from "@/features/connections/components/property-picker";
import { connectionsApi, GA4Property, GoogleAnalyticsStatusResponse } from "@/lib/api/connections";
```

Note: `connectionsApi` is already imported — just add the types.

- [ ] **Step 2: Add property picker state to GoogleWorkspaceView (after existing state, ~line 229)**

```tsx
  // GA4 Property Picker State
  const [gaStatus, setGaStatus] = useState<GoogleAnalyticsStatusResponse | null>(null);
  const [ga4Properties, setGa4Properties] = useState<GA4Property[]>([]);
  const [showGaPropertyPicker, setShowGaPropertyPicker] = useState(false);
  const [loadingGaProperties, setLoadingGaProperties] = useState(false);
```

- [ ] **Step 3: Add GA status check in the `onSuccess` callback (~line 252-268)**

After `await fetchStatus();` (line 262), add:

```tsx
        // Check if GA needs property selection
        try {
          const gaData = await connectionsApi.getGoogleAnalyticsStatus(token!);
          setGaStatus(gaData);
          if (gaData.is_connected && !gaData.selected_property) {
            // Try to use properties from workspace callback
            const wsResult = await connectionsApi.getGoogleAnalyticsProperties(token!);
            setGa4Properties(wsResult);
            setShowGaPropertyPicker(true);
          }
        } catch (e) {
          console.error("Could not check GA status after workspace connect", e);
        }
```

- [ ] **Step 4: Add helper functions before the return statements**

```tsx
  const handleChangeGaProperty = async () => {
    try {
      setLoadingGaProperties(true);
      const token = await getToken();
      if (!token) return;
      const props = await connectionsApi.getGoogleAnalyticsProperties(token);
      setGa4Properties(props);
      setShowGaPropertyPicker(true);
    } catch (error: any) {
      console.error(error);
      toast.error("Error al obtener propiedades de GA4");
      setGa4Properties([]);
      setShowGaPropertyPicker(true);
    } finally {
      setLoadingGaProperties(false);
    }
  };

  const handleGaPropertySelected = async () => {
    setShowGaPropertyPicker(false);
    const token = await getToken();
    if (token) {
      const gaData = await connectionsApi.getGoogleAnalyticsStatus(token);
      setGaStatus(gaData);
    }
  };
```

- [ ] **Step 5: Add GA property picker section in the connected view**

In the connected view's `<CardContent>` (after the services map, ~line 420-428), add before the closing `</CardContent>`:

```tsx
        {/* GA4 Property Picker */}
        {showGaPropertyPicker && (
          <>
            <Separator className="my-4" />
            <PropertyPicker
              properties={ga4Properties}
              onSelected={handleGaPropertySelected}
              isChangeMode={!!gaStatus?.selected_property}
            />
          </>
        )}

        {/* GA4 Property Status (when connected but picker not open) */}
        {!showGaPropertyPicker && gaStatus?.is_connected && !gaStatus?.selected_property && (
          <>
            <Separator className="my-4" />
            <Alert className="bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-200 dark:border-amber-800">
              <BarChart className="h-4 w-4" />
              <AlertDescription className="text-xs">
                Google Analytics está conectado pero falta seleccionar una propiedad.{" "}
                <button
                  type="button"
                  onClick={handleChangeGaProperty}
                  className="underline font-medium hover:text-foreground"
                >
                  Seleccionar ahora
                </button>
              </AlertDescription>
            </Alert>
          </>
        )}

        {!showGaPropertyPicker && gaStatus?.selected_property && (
          <>
            <Separator className="my-4" />
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">
                GA4: <strong className="text-foreground">{gaStatus.selected_property.display_name}</strong>
              </span>
              <button
                type="button"
                onClick={handleChangeGaProperty}
                disabled={loadingGaProperties}
                className="text-muted-foreground underline hover:text-foreground"
              >
                {loadingGaProperties ? "Cargando..." : "Cambiar"}
              </button>
            </div>
          </>
        )}
```

- [ ] **Step 6: Add `useEffect` to fetch GA status on mount (connected state)**

After the existing `useEffect` for `fetchStatus` (~line 247):

```tsx
  // Check GA property status when workspace is connected
  useEffect(() => {
    if (status?.is_connected) {
      const checkGa = async () => {
        try {
          const token = await getToken();
          if (!token) return;
          const gaData = await connectionsApi.getGoogleAnalyticsStatus(token);
          setGaStatus(gaData);
        } catch (e) {
          // Silently ignore — GA status is supplementary
        }
      };
      checkGa();
    }
  }, [status?.is_connected]); // eslint-disable-line react-hooks/exhaustive-deps
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/connections/components/google-workspace-view.tsx
git commit -m "feat(connections): integrate GA4 PropertyPicker in Workspace view"
```

---

### Task 9: Smoke test in Docker

- [ ] **Step 1: Build and run backend**

```bash
docker exec -it visionarias_brain_dev bash -c "cd /app && python -c 'from src.modules.connections.api.google_analytics import router; print(\"Router OK\")'"
```

Expected: `Router OK` (no import errors)

- [ ] **Step 2: Build frontend**

```bash
docker exec -it visionarias_client_dev bash -c "cd /app && npx tsc --noEmit 2>&1 | head -30"
```

Expected: No new TypeScript errors from our changes.

- [ ] **Step 3: Test the /status endpoint returns new shape**

```bash
# Use curl from brain container — replace TOKEN with a valid Clerk JWT
docker exec -it visionarias_brain_dev bash -c "curl -s http://localhost:8000/api/v1/connections/google-analytics/status -H 'Authorization: Bearer TOKEN' | python3 -m json.tool"
```

Expected: Response includes `is_configured`, `selected_property` fields.

- [ ] **Step 4: Final commit with any fixes**

```bash
git add -A
git commit -m "fix: address smoke test findings"
```
