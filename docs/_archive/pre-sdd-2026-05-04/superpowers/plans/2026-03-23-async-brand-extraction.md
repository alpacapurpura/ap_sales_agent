# Async Brand Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the synchronous brand extraction endpoint to an async ARQ job with real-time polling, fixing Cloudflare's 100s timeout that kills the 144s request.

**Architecture:** POST /extract-full-brand enqueues an ARQ job and returns 202 + job_id immediately. The worker executes the extraction and writes progress to Redis after each wave. Frontend polls GET /status/{job_id} every 3s for real progress.

**Tech Stack:** FastAPI, ARQ (Redis job queue), Redis (progress storage), Next.js 14, React 18

**Spec:** `docs/superpowers/specs/2026-03-23-async-brand-extraction-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/src/main.py` | Modify | ARQ pool startup/shutdown lifecycle |
| `backend/src/modules/brand/workers/__init__.py` | Create | Package init |
| `backend/src/modules/brand/workers/tasks.py` | Create | ARQ task `run_brand_extraction` with Redis progress |
| `backend/src/modules/brand/application/extraction_service.py` | Modify | Add `progress_callback` to `extract_all()` |
| `backend/src/modules/copilot/application/services/brand_ai_actions_service.py` | Modify | Forward `progress_callback` |
| `backend/src/modules/brand/api/extraction.py` | Modify | POST returns 202; new GET /status endpoint |
| `backend/src/modules/analytics/workers/settings.py` | Modify | Register brand task |
| `frontend/src/lib/api/ai-actions.ts` | Modify | POST + poll replacing sync fetch |
| `frontend/src/features/brand/api/index.ts` | Modify | Update brandApi wrapper for new return types |
| `frontend/src/features/brand/components/smart-fill/smart-fill-dialog.tsx` | Modify | Real progress from polling |

---

### Task 1: ARQ Pool Lifecycle in main.py

**Files:**
- Modify: `backend/src/main.py:103-109`

- [ ] **Step 1: Add ARQ pool startup event**

In `backend/src/main.py`, add a new async startup event after the existing sync one (line 109). The existing `on_startup` is sync (`def`), so add a separate async event for ARQ:

```python
# Add these imports at the top of main.py (after existing imports):
from arq.connections import create_pool, RedisSettings

# Add after line 109 (after the existing on_startup):
@app.on_event("startup")
async def startup_arq_pool():
    """Create shared ARQ connection pool for job dispatch."""
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))

@app.on_event("shutdown")
async def shutdown_arq_pool():
    """Close ARQ connection pool."""
    if hasattr(app.state, "arq_pool") and app.state.arq_pool:
        await app.state.arq_pool.close()
```

- [ ] **Step 2: Verify app starts without errors**

Run: `docker exec -t visionarias_brain_dev python -c "from src.main import app; print('OK')"`
Expected: `OK` (no import errors)

- [ ] **Step 3: Commit**

```bash
git add backend/src/main.py
git commit -m "feat(brand): add shared ARQ pool lifecycle to FastAPI app"
```

---

### Task 2: Progress Callback in BrandExtractionService

**Files:**
- Modify: `backend/src/modules/brand/application/extraction_service.py:603-791`
- Modify: `backend/src/modules/copilot/application/services/brand_ai_actions_service.py:22-38`

- [ ] **Step 1: Add progress_callback parameter to extract_all()**

In `backend/src/modules/brand/application/extraction_service.py`, modify the `extract_all` method signature at line 603:

```python
# Change from:
async def extract_all(
    self,
    url: Optional[str] = None,
    text: Optional[str] = None,
    mode: Literal["initial", "update"] = "initial",
    update_instructions: Optional[str] = None,
    dry_run: bool = False,
    include_visuals: bool = False
) -> BrandSettings:

# Change to:
async def extract_all(
    self,
    url: Optional[str] = None,
    text: Optional[str] = None,
    mode: Literal["initial", "update"] = "initial",
    update_instructions: Optional[str] = None,
    dry_run: bool = False,
    include_visuals: bool = False,
    progress_callback: Optional["Callable[[int, str], None]"] = None,
) -> BrandSettings:
```

Add `Callable` to the typing import at line 1:

```python
from typing import Optional, Literal, List, Callable
```

- [ ] **Step 2: Insert callback calls at phase boundaries**

Inside `extract_all()`, add callback invocations. After the parallel crawl completes (after line 651):

```python
            if progress_callback:
                progress_callback(10, "Escaneando sitio web...")
```

In the `waves >= 2` branch — after wave 1 gather completes (after line 702):

```python
            if progress_callback:
                progress_callback(45, "Analizando identidad y visual...")
```

After wave 2 gather completes (after line 717):

```python
            if progress_callback:
                progress_callback(80, "Extrayendo estrategia y posicionamiento...")
```

After wave 3 (communication_assets) completes (after line 730):

```python
            if progress_callback:
                progress_callback(95, "Generando activos de comunicación...")
```

In the `else` branch (all concurrent, `waves < 2`) — after the main gather (after line 751):

```python
            if progress_callback:
                progress_callback(80, "Extrayendo secciones...")
```

After communication_assets in the else branch (after line 759):

```python
            if progress_callback:
                progress_callback(95, "Generando activos de comunicación...")
```

- [ ] **Step 3: Forward progress_callback through CopilotBrandAIActionsService**

In `backend/src/modules/copilot/application/services/brand_ai_actions_service.py`, modify `extract_full_brand` at line 22:

```python
# Change from:
async def extract_full_brand(
    self,
    url: Optional[str] = None,
    text: Optional[str] = None,
    mode: Literal["initial", "update"] = "initial",
    update_instructions: Optional[str] = None,
    dry_run: bool = False,
    include_visuals: bool = False,
) -> BrandSettings:
    return await self.brand_extraction_service.extract_all(
        url=url,
        text=text,
        mode=mode,
        update_instructions=update_instructions,
        dry_run=dry_run,
        include_visuals=include_visuals,
    )

# Change to:
async def extract_full_brand(
    self,
    url: Optional[str] = None,
    text: Optional[str] = None,
    mode: Literal["initial", "update"] = "initial",
    update_instructions: Optional[str] = None,
    dry_run: bool = False,
    include_visuals: bool = False,
    progress_callback=None,
) -> BrandSettings:
    return await self.brand_extraction_service.extract_all(
        url=url,
        text=text,
        mode=mode,
        update_instructions=update_instructions,
        dry_run=dry_run,
        include_visuals=include_visuals,
        progress_callback=progress_callback,
    )
```

- [ ] **Step 4: Verify no regressions (existing callers pass no callback)**

Run: `docker exec -t visionarias_brain_dev python -c "from src.modules.brand.application.extraction_service import BrandExtractionService; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/brand/application/extraction_service.py backend/src/modules/copilot/application/services/brand_ai_actions_service.py
git commit -m "feat(brand): add progress_callback to extraction service"
```

---

### Task 3: ARQ Task for Brand Extraction

**Files:**
- Create: `backend/src/modules/brand/workers/__init__.py`
- Create: `backend/src/modules/brand/workers/tasks.py`

- [ ] **Step 1: Create the workers package**

Create `backend/src/modules/brand/workers/__init__.py` (empty file).

- [ ] **Step 2: Create the ARQ task**

Create `backend/src/modules/brand/workers/tasks.py`:

```python
"""ARQ task for async brand extraction with Redis progress tracking."""

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

logger = logging.getLogger(__name__)


async def run_brand_extraction(
    ctx: dict,
    job_id: str,
    tenant_id: str,
    url: str | None,
    text: str | None,
    mode: str,
    update_instructions: str | None,
    include_visuals: bool,
    dry_run: bool = False,
) -> dict:
    """Execute brand extraction as a background job.

    Writes progress to Redis at each extraction wave so the frontend
    can poll for real-time updates.
    """
    db_factory = ctx["db_factory"]
    db = db_factory()
    redis = ctx.get("redis")
    progress_key = f"brand_extract:{tenant_id}:{job_id}"

    def on_progress(progress_pct: int, stage: str):
        if redis:
            redis.setex(
                progress_key, 3600,
                json.dumps({
                    "status": "processing",
                    "progress": progress_pct,
                    "stage": stage,
                    "started_at": started_at,
                }),
            )

    started_at = datetime.now(timezone.utc).isoformat()

    try:
        # Late imports to avoid circular dependencies
        from src.modules.copilot.application.services.brand_ai_actions_service import (
            CopilotBrandAIActionsService,
        )

        on_progress(5, "Iniciando análisis...")

        service = CopilotBrandAIActionsService(db, UUID(tenant_id))
        await service.extract_full_brand(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            dry_run=dry_run,
            include_visuals=include_visuals,
            progress_callback=on_progress,
        )

        # Mark completed
        if redis:
            redis.setex(
                progress_key, 3600,
                json.dumps({
                    "status": "completed",
                    "progress": 100,
                    "stage": "¡Análisis completado!",
                }),
            )

        logger.info(
            "Brand extraction completed for tenant=%s job=%s",
            tenant_id, job_id,
        )
        return {"status": "success", "tenant_id": tenant_id, "job_id": job_id}

    except Exception as exc:
        logger.error(
            "Brand extraction failed for tenant=%s job=%s: %s",
            tenant_id, job_id, str(exc),
        )
        if redis:
            redis.setex(
                progress_key, 3600,
                json.dumps({
                    "status": "failed",
                    "progress": 0,
                    "error": f"{type(exc).__name__}: {str(exc)[:200]}",
                }),
            )
        return {"status": "failed", "tenant_id": tenant_id, "error": str(exc)}

    finally:
        db.close()
```

- [ ] **Step 3: Verify import works**

Run: `docker exec -t visionarias_brain_dev python -c "from src.modules.brand.workers.tasks import run_brand_extraction; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/brand/workers/
git commit -m "feat(brand): add ARQ task for async brand extraction"
```

---

### Task 4: Register Brand Task in Worker Settings

**Files:**
- Modify: `backend/src/modules/analytics/workers/settings.py:13-24`

- [ ] **Step 1: Add import and register task**

In `backend/src/modules/analytics/workers/settings.py`, add the import after the existing analytics imports (after line 18):

```python
from src.modules.brand.workers.tasks import run_brand_extraction
```

Add `run_brand_extraction` to the `functions` list in `WorkerSettings` (line 24):

```python
functions = [run_tenant_extraction, run_initial_load, run_inactivity_detection, run_mailerlite_etl_sync, run_brand_extraction]
```

And to `SchedulerSettings.functions` (line 61):

```python
functions = [run_tenant_extraction, run_initial_load, run_inactivity_detection, run_mailerlite_etl_sync, run_brand_extraction]
```

- [ ] **Step 2: Verify worker settings load**

Run: `docker exec -t visionarias_brain_dev python -c "from src.modules.analytics.workers.settings import WorkerSettings; print(len(WorkerSettings.functions), 'functions')"`
Expected: `5 functions`

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/analytics/workers/settings.py
git commit -m "feat(brand): register brand extraction task in ARQ worker"
```

---

### Task 5: Modify POST Endpoint + Add Status Endpoint

**Files:**
- Modify: `backend/src/modules/brand/api/extraction.py`

- [ ] **Step 1: Rewrite the POST endpoint to dispatch async job**

Replace the full `extract_full_brand` function (lines 46-133) in `backend/src/modules/brand/api/extraction.py`:

```python
@router.post("/extract-full-brand")
async def extract_full_brand(
    request: Request,
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    mode: Literal["initial", "update"] = Form("initial"),
    update_instructions: Optional[str] = Form(None),
    dry_run: bool = Form(False),
    include_visuals: bool = Form(False),
    files: list[UploadFile] = File(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dispatches full brand extraction as an async job.
    Returns 202 with job_id for polling via GET /extract-full-brand/status/{job_id}.
    """
    from uuid import uuid4
    from datetime import datetime, timezone
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from src.core.database import redis_client

    # Parse uploaded files (UploadFile can't be serialized to ARQ)
    extracted_file_text = ""
    for file in files:
        content = await FileParsingService.parse_file(file)
        if content:
            extracted_file_text += f"\n--- Documento adjunto: {file.filename} ---\n{content}\n"

    combined_text = (text or "") + "\n" + extracted_file_text
    combined_text = combined_text.strip()

    if not url and not combined_text and not update_instructions:
        raise HTTPException(status_code=400, detail="Either 'url', 'text', 'files', or 'update_instructions' must be provided.")

    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant.")

    # Check Redis availability
    if not redis_client:
        raise HTTPException(status_code=503, detail="Servicio temporalmente no disponible. Intenta en un momento.")

    job_id = str(uuid4())
    tenant_id = str(current_user.tenant_id)

    logger.info("extract_full_brand_request",
                tenant_id=tenant_id,
                job_id=job_id,
                has_url=bool(url),
                url=url,
                mode=mode,
                has_text=bool(combined_text),
                text_length=len(combined_text) if combined_text else 0,
                file_count=len(files),
                has_instructions=bool(update_instructions),
                dry_run=dry_run)

    # 1. Set initial status in Redis BEFORE enqueue (prevents race condition)
    redis_client.setex(
        f"brand_extract:{tenant_id}:{job_id}",
        3600,
        json.dumps({
            "status": "queued",
            "progress": 0,
            "stage": "Iniciando análisis...",
            "started_at": datetime.now(timezone.utc).isoformat(),
        })
    )

    # 2. Enqueue ARQ job
    arq_pool = request.app.state.arq_pool
    await arq_pool.enqueue_job(
        "run_brand_extraction",
        job_id=job_id,
        tenant_id=tenant_id,
        url=url,
        text=combined_text if combined_text else None,
        mode=mode,
        update_instructions=update_instructions,
        include_visuals=include_visuals,
        dry_run=dry_run,
    )

    logger.info("extract_full_brand_dispatched", tenant_id=tenant_id, job_id=job_id)

    return JSONResponse(status_code=202, content={"job_id": job_id, "status": "queued"})
```

- [ ] **Step 2: Add the status polling endpoint**

Add after the POST endpoint in the same file:

```python
@router.get("/extract-full-brand/status/{job_id}")
async def get_extraction_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Poll extraction job progress. Returns status, progress %, and current stage."""
    from uuid import UUID as UUIDType
    from datetime import datetime, timezone
    from src.core.database import redis_client

    # Validate job_id format
    try:
        UUIDType(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    progress_key = f"brand_extract:{current_user.tenant_id}:{job_id}"
    raw = redis_client.get(progress_key) if redis_client else None

    if not raw:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    data = json.loads(raw)

    # Stale job detection: if processing for >10 minutes, mark as failed
    if data.get("status") in ("processing", "queued") and data.get("started_at"):
        try:
            started = datetime.fromisoformat(data["started_at"])
            if (datetime.now(timezone.utc) - started).total_seconds() > 600:
                data["status"] = "failed"
                data["error"] = "El proceso no respondió. Intenta de nuevo."
        except (ValueError, TypeError):
            pass

    return data
```

- [ ] **Step 3: Add all missing imports at the top of the file**

Add to the imports at the top of `extraction.py` (and remove the in-function imports from Steps 1 and 2):

```python
import json
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from src.core.database import redis_client
```

- [ ] **Step 4: Verify endpoints load**

Run: `docker exec -t visionarias_brain_dev python -c "from src.modules.brand.api.extraction import router; print([r.path for r in router.routes])"`
Expected: List including `/extract-full-brand` and `/extract-full-brand/status/{job_id}`

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/brand/api/extraction.py
git commit -m "feat(brand): POST returns 202 + job_id, add GET /status polling endpoint"
```

---

### Task 6: Frontend API Layer — POST + Poll

**Files:**
- Modify: `frontend/src/lib/api/ai-actions.ts`

- [ ] **Step 1: Add ExtractionStatus type and pollExtractionStatus method**

In `frontend/src/lib/api/ai-actions.ts`, add the type after the existing interfaces (after line 31):

```typescript
export interface ExtractionStatus {
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  stage?: string;
  error?: string;
}
```

- [ ] **Step 2: Replace extractFullBrand and add pollExtractionStatus**

Replace the `extractFullBrand` method (lines 63-93) with:

```typescript
  async extractFullBrand(input: FullBrandExtractInput, token: string): Promise<{ job_id: string }> {
    const body = toFormData(input);
    const response = await fetchClient(`${API_URL}/api/v1/brand/tools/extract-full-brand`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body,
    });

    if (!response.ok) {
      throw new Error(`Failed to start extraction: ${response.status} ${response.statusText}`);
    }
    return response.json();
  },

  async pollExtractionStatus(jobId: string, token: string): Promise<ExtractionStatus> {
    const response = await fetchClient(
      `${API_URL}/api/v1/brand/tools/extract-full-brand/status/${jobId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    if (!response.ok) throw new Error(`Status check failed: ${response.status}`);
    return response.json();
  },
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api/ai-actions.ts
git commit -m "feat(brand): replace sync fetch with POST + poll in API layer"
```

---

### Task 7: Update brandApi Wrapper

**Files:**
- Modify: `frontend/src/features/brand/api/index.ts:75-88`

- [ ] **Step 1: Replace extractFullBrand and add pollExtractionStatus**

In `frontend/src/features/brand/api/index.ts`, replace the `extractFullBrand` method (lines 75-88) and add `pollExtractionStatus`:

```typescript
    extractFullBrand: async (data: FullBrandExtractionRequest | FormData, token: string): Promise<{ job_id: string }> => {
        const result = await aiActionsApi.extractFullBrand(data, token);
        return result as { job_id: string };
    },

    pollExtractionStatus: async (jobId: string, token: string) => {
        return aiActionsApi.pollExtractionStatus(jobId, token);
    },
```

- [ ] **Step 2: Add ExtractionStatus re-export**

Add to the import at line 3:

```typescript
import { aiActionsApi, ExtractionStatus } from "@/lib/api/ai-actions";
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/brand/api/index.ts
git commit -m "feat(brand): update brandApi wrapper for async extraction"
```

---

### Task 8: SmartFill Dialog — Real Progress from Polling

**Files:**
- Modify: `frontend/src/features/brand/components/smart-fill/smart-fill-dialog.tsx`

- [ ] **Step 1: Add useRef and useEffect imports and refs**

At line 3, add `useRef, useEffect` to the React import:

```typescript
import { useState, useRef, useEffect } from "react";
```

Inside the component (after line 49, after the `errorState` state), add:

```typescript
    const activeJobRef = useRef<string | null>(null);
    const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            activeJobRef.current = null;
            if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
        };
    }, []);
```

- [ ] **Step 2: Replace handleExtract with async polling version**

Replace the `handleExtract` function (lines 58-152) with:

```typescript
    const handleExtract = async () => {
        if (sourceType === "web" && !url) {
            toast.error("Por favor ingresa una URL válida.");
            return;
        }
        if (sourceType === "manual" && !text && files.length === 0 && !instructions) {
            toast.error("Ingresa texto, sube archivos o escribe instrucciones.");
            return;
        }

        try {
            const token = await getToken();
            if (!token) {
                toast.error("No autenticado");
                return;
            }

            setIsProcessing(true);
            setErrorState(null);
            setProgress(0);
            setStage("Iniciando análisis...");

            // Prepare FormData
            const formData = new FormData();
            formData.append("mode", mode);

            if (sourceType === "web") {
                formData.append("url", url);
            } else {
                if (text) formData.append("text", text);
                files.forEach(file => formData.append("files", file));
            }

            if (instructions) formData.append("update_instructions", instructions);

            // 1. Start async job
            const { job_id } = await brandApi.extractFullBrand(formData, token);
            activeJobRef.current = job_id;

            // 2. Poll with setTimeout chain (avoids overlapping requests)
            const poll = async () => {
                if (activeJobRef.current !== job_id) return;

                try {
                    const status = await brandApi.pollExtractionStatus(job_id, token);
                    if (activeJobRef.current !== job_id) return;

                    setProgress(status.progress);
                    if (status.stage) setStage(status.stage);

                    if (status.status === "completed") {
                        toast.success(mode === "initial"
                            ? "¡Marca generada exitosamente!"
                            : "¡Marca actualizada exitosamente!");

                        setTimeout(() => {
                            resetForm();
                            onOpenChange(false);
                            onSuccess();
                        }, 800);
                        return;
                    }

                    if (status.status === "failed") {
                        setErrorState({
                            type: "generic",
                            message: status.error || "Error desconocido en la extracción"
                        });
                        setStage("Proceso interrumpido");
                        setProgress(0);
                        setIsProcessing(false);
                        return;
                    }
                } catch (err) {
                    console.warn("[SmartFill] Poll error, retrying:", err);
                }

                pollTimerRef.current = setTimeout(poll, 3000);
            };

            pollTimerRef.current = setTimeout(poll, 1000);

        } catch (error: any) {
            console.error("[SmartFill] Error starting extraction:", error);
            setErrorState({
                type: "generic",
                message: error.message || "Error al iniciar la extracción"
            });
            setStage("Proceso interrumpido");
            setProgress(0);
            setIsProcessing(false);
        }
    };
```

- [ ] **Step 3: Simplify error state type (remove "timeout" variant)**

Change the `errorState` type at line 49 from:

```typescript
const [errorState, setErrorState] = useState<{ type: "timeout" | "generic", message: string } | null>(null);
```

To:

```typescript
const [errorState, setErrorState] = useState<{ type: "generic", message: string } | null>(null);
```

In the JSX, remove the timeout-specific rendering (lines 182-202). Replace the entire error Alert block with:

```tsx
{errorState && (
    <Alert variant="destructive" className="animate-in shake">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error en el análisis</AlertTitle>
        <AlertDescription className="mt-2 text-sm">
            {errorState.message}
        </AlertDescription>
        <div className="mt-4">
            <Button variant="outline" size="sm" onClick={() => setErrorState(null)} className="bg-background/50">
                Intentar de nuevo
            </Button>
        </div>
    </Alert>
)}
```

- [ ] **Step 4: Remove unused WifiOff import**

Remove `WifiOff` from the lucide-react import at line 15 (it was only used for the timeout error icon).

- [ ] **Step 5: Verify TypeScript compiles**

Run: `docker exec -t visionarias_client_dev npx tsc --noEmit --pretty 2>&1 | grep -E 'smart-fill|ai-actions' | head -10`
Expected: No errors related to these files

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/api/ai-actions.ts frontend/src/features/brand/components/smart-fill/smart-fill-dialog.tsx
git commit -m "feat(brand): real-time polling in SmartFill dialog with cleanup on unmount"
```

---

### Task 9: Integration Test in Dev Docker

**Files:** None (manual verification)

- [ ] **Step 1: Ensure worker is running**

Run: `docker compose --profile extended up -d`
Verify: `docker ps | grep visionarias_worker`

- [ ] **Step 2: Test POST returns 202**

```bash
# Get a token from Clerk (or use the browser network tab to grab one)
# Then test the endpoint:
docker exec -t visionarias_brain_dev python -c "
import asyncio, json
from httpx import AsyncClient

async def test():
    async with AsyncClient(base_url='http://localhost:8000') as client:
        resp = await client.post(
            '/api/v1/brand/tools/extract-full-brand',
            data={'url': 'https://alpacapurpura.lat/', 'mode': 'update'},
            headers={'X-Tenant-ID': '39799d54-9449-4f7a-a2b2-20ca3196e37a',
                     'Authorization': 'Bearer TEST_TOKEN'}
        )
        print(f'Status: {resp.status_code}')
        print(f'Body: {resp.text}')

asyncio.run(test())
"
```

Expected: `Status: 202` with `{"job_id": "...", "status": "queued"}`

(Note: This will fail auth without a real Clerk token. The real test is via the browser UI.)

- [ ] **Step 3: Test full flow via browser**

1. Open the app in browser (dev)
2. Go to Brand Studio
3. Click "Refinar con IA"
4. Enter URL and submit
5. Verify: progress bar shows real stages, completes without "timeout" error
6. Verify: brand data loads after completion

- [ ] **Step 4: Test dialog close mid-extraction**

1. Start an extraction
2. Close the dialog while it's processing
3. Wait for it to finish (check worker logs: `docker logs visionarias_worker -f`)
4. Reopen Brand Studio — data should be there

- [ ] **Step 5: Final commit with any fixes**

```bash
git add -A
git commit -m "fix(brand): integration fixes for async extraction"
```
