# Async Brand Extraction with Real-Time Polling

**Date:** 2026-03-23
**Status:** Reviewed
**Problem:** Cloudflare's 100-120s proxy read timeout kills the synchronous brand extraction request (~144s), causing a false "timeout" error in the frontend even though the backend completes successfully and saves to DB.

## Solution

Convert `POST /extract-full-brand` from a synchronous endpoint to an async job dispatched via ARQ (existing worker infrastructure). The frontend polls a new status endpoint every 3 seconds to get real progress updates.

## Architecture

### Current Flow (Broken)
```
Browser → POST /extract-full-brand → Cloudflare → Backend (144s processing)
                                        ↑
                                   100s: Cloudflare cuts → "Failed to fetch"
                                        Backend continues, saves to DB (orphaned response)
```

### New Flow
```
Browser → POST /extract-full-brand → Backend returns 202 + job_id (<1s)
Browser → GET /extract-full-brand/status/{job_id} (every 3s, each <1s)
         → {status: "processing", progress: 45, stage: "Analizando identidad..."}
         → {status: "completed", progress: 100}
Browser → Reloads brand settings from GET /brand/settings
```

No single HTTP request exceeds 1-2 seconds. Cloudflare timeout is irrelevant.

## Backend Changes

### 1. New ARQ Task: `run_brand_extraction`

**File:** `backend/src/modules/brand/workers/tasks.py` (new file)

```python
async def run_brand_extraction(
    ctx: dict,
    job_id: str,
    tenant_id: str,
    url: str | None,
    text: str | None,
    mode: str,  # "initial" | "update"
    update_instructions: str | None,
    include_visuals: bool,
    dry_run: bool = False,
) -> dict:
```

**Behavior:**
- Reads `db_factory` and `redis` from ARQ context (same pattern as `run_initial_load`)
- Routes through `CopilotBrandAIActionsService` for consistency with current endpoint (not `BrandExtractionService` directly — the wrapper may add pre/post-processing in the future)
- Passes a `progress_callback` that writes to Redis after each phase:
  - Key: `brand_extract:{tenant_id}:{job_id}`
  - TTL: 3600s (1 hour, auto-cleanup)
  - Value: `{"status": "processing", "progress": 45, "stage": "...", "started_at": "ISO8601"}`
- On success: sets status to `"completed"` with `progress: 100`
- On failure: sets status to `"failed"` with `error` message
- Does NOT retry (unlike ETL tasks) — brand extraction is user-initiated and idempotent

**Progress stages (maps to extraction waves):**

| Phase | Progress | Stage |
|---|---|---|
| Queued | 0 | Iniciando análisis... |
| Crawling | 10 | Escaneando sitio web... |
| Wave 1 complete | 45 | Analizando identidad y visual... |
| Wave 2 complete | 80 | Extrayendo estrategia y posicionamiento... |
| Wave 3 complete | 95 | Generando activos de comunicación... |
| Saved to DB | 100 | ¡Análisis completado! |

### 2. Modified Endpoint: `POST /extract-full-brand`

**File:** `backend/src/modules/brand/api/extraction.py`

Changes:
- Keep all existing validation and file parsing logic (lines 47-89 unchanged)
- Remove `response_model=BrandSettings` from decorator (now returns job metadata, not BrandSettings)
- Instead of `await service.extract_full_brand(...)`, enqueue an ARQ job
- Return `202 Accepted` with `{"job_id": "...", "status": "queued"}`
- The `combined_text` from file parsing is passed as a string to the ARQ job (UploadFile objects can't be serialized to Redis)

**IMPORTANT: Write Redis key BEFORE enqueue to prevent race condition** (worker could start and overwrite progress before the endpoint sets initial state):

```python
from uuid import uuid4
from src.core.database import redis_client

job_id = str(uuid4())

# 1. Set initial status FIRST (prevents race with worker)
redis_client.setex(
    f"brand_extract:{current_user.tenant_id}:{job_id}",
    3600,
    json.dumps({
        "status": "queued",
        "progress": 0,
        "stage": "Iniciando análisis...",
        "started_at": datetime.now(timezone.utc).isoformat(),
    })
)

# 2. THEN enqueue the job
arq_pool = request.app.state.arq_pool  # shared pool, see section 2a
await arq_pool.enqueue_job(
    "run_brand_extraction",
    job_id=job_id,
    tenant_id=str(current_user.tenant_id),
    url=url,
    text=combined_text if combined_text else None,
    mode=mode,
    update_instructions=update_instructions,
    include_visuals=include_visuals,
    dry_run=dry_run,
)

return JSONResponse(status_code=202, content={"job_id": job_id, "status": "queued"})
```

### 2a. Shared ARQ Pool (avoid per-request pool creation)

**File:** `backend/src/main.py` (app startup)

Create the ARQ pool once at startup, store in `app.state`:

```python
from arq.connections import create_pool, RedisSettings

@app.on_event("startup")
async def startup_arq_pool():
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))

@app.on_event("shutdown")
async def shutdown_arq_pool():
    await app.state.arq_pool.close()
```

The endpoint accesses it via `request.app.state.arq_pool` (inject `request: Request` as a FastAPI parameter).

### 3. New Endpoint: `GET /extract-full-brand/status/{job_id}`

**File:** `backend/src/modules/brand/api/extraction.py`

```python
@router.get("/extract-full-brand/status/{job_id}")
async def get_extraction_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    # Validate job_id is a valid UUID (prevent malformed keys)
    try:
        UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    progress_key = f"brand_extract:{current_user.tenant_id}:{job_id}"
    raw = redis_client.get(progress_key)
    if not raw:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    data = json.loads(raw)

    # Stale job detection: if processing for >10 minutes, mark as failed
    if data.get("status") == "processing" and data.get("started_at"):
        started = datetime.fromisoformat(data["started_at"])
        if (datetime.now(timezone.utc) - started).total_seconds() > 600:
            data["status"] = "failed"
            data["error"] = "El proceso no respondió. Intenta de nuevo."

    return data
```

Response shapes:
```json
{"status": "queued", "progress": 0, "stage": "Iniciando análisis...", "started_at": "..."}
{"status": "processing", "progress": 45, "stage": "Analizando identidad...", "started_at": "..."}
{"status": "completed", "progress": 100, "stage": "¡Análisis completado!"}
{"status": "failed", "progress": 0, "error": "Error message here"}
```

### 4. Register Task in Worker Settings

**File:** `backend/src/modules/analytics/workers/settings.py`

Add `run_brand_extraction` to both `WorkerSettings.functions` and `SchedulerSettings.functions` lists.

> **Note on DDD boundaries:** The analytics worker is already a de-facto platform worker (it runs `run_inactivity_detection` from CRM and `run_mailerlite_etl_sync` from connections). Adding a brand task follows the established pattern. A rename to `platform_worker` is a separate future refactor.

### 5. Progress Callback in BrandExtractionService

**File:** `backend/src/modules/brand/application/extraction_service.py`

Add an optional `progress_callback` parameter to `extract_all()`:

```python
from typing import Callable, Optional

ProgressCallback = Callable[[int, str], None]  # (progress_pct, stage_message)

async def extract_all(self, ..., progress_callback: Optional[ProgressCallback] = None):
```

Insert callback calls at each phase boundary:
- After crawling: `if progress_callback: progress_callback(10, "Escaneando sitio web...")`
- After wave 1: `if progress_callback: progress_callback(45, "Analizando identidad y visual...")`
- After wave 2: `if progress_callback: progress_callback(80, "Extrayendo estrategia y posicionamiento...")`
- After wave 3: `if progress_callback: progress_callback(95, "Generando activos de comunicación...")`

The callback is optional — when `None`, the service behaves exactly as today. No regression for direct callers or `CopilotBrandAIActionsService`.

The `progress_callback` also needs to be threaded through `CopilotBrandAIActionsService.extract_full_brand()` as an optional param that forwards to `extract_all()`.

### 6. Redis Unavailability Fallback

If `redis_client` is unavailable when the POST endpoint tries to set the initial key, return **503 Service Unavailable** with a retry message — do NOT fall back to synchronous execution (that would reintroduce the Cloudflare timeout problem).

```python
if not redis_client:
    raise HTTPException(status_code=503, detail="Servicio temporalmente no disponible. Intenta en un momento.")
```

## Frontend Changes

### 1. API Layer: Replace Sync Fetch with POST + Poll

**File:** `frontend/src/lib/api/ai-actions.ts`

Replace `extractFullBrand()` and add `pollExtractionStatus()`:

```typescript
async extractFullBrand(input: FullBrandExtractInput, token: string): Promise<{ job_id: string }> {
    const body = toFormData(input);
    const response = await fetchClient(`${API_URL}/api/v1/brand/tools/extract-full-brand`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
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
        { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) throw new Error(`Status check failed: ${response.status}`);
    return response.json();
}
```

New type:
```typescript
interface ExtractionStatus {
    status: "queued" | "processing" | "completed" | "failed";
    progress: number;
    stage?: string;
    error?: string;
}
```

**Removals:**
- Remove the `AbortController` with 480s timeout
- Remove the 504 status check → "TIMEOUT:" error
- Remove the AbortError catch

### 2. SmartFill Dialog: Real Progress from Polling

**File:** `frontend/src/features/brand/components/smart-fill/smart-fill-dialog.tsx`

Replace `handleExtract` internals:

```typescript
// Track active job to ignore stale polls
const activeJobRef = useRef<string | null>(null);
const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

// Cleanup on unmount or dialog close
useEffect(() => {
    return () => {
        activeJobRef.current = null;
        if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
}, []);

const handleExtract = async () => {
    // ... existing validation ...

    const token = await getToken();
    setIsProcessing(true);
    setErrorState(null);
    setProgress(0);
    setStage("Iniciando análisis...");

    // 1. Start job (returns immediately)
    const { job_id } = await brandApi.extractFullBrand(formData, token);
    activeJobRef.current = job_id;

    // 2. Poll with setTimeout chain (not setInterval — avoids overlapping requests)
    const poll = async () => {
        if (activeJobRef.current !== job_id) return; // stale job, stop

        try {
            const status = await brandApi.pollExtractionStatus(job_id, token);
            if (activeJobRef.current !== job_id) return;

            setProgress(status.progress);
            if (status.stage) setStage(status.stage);

            if (status.status === "completed") {
                toast.success(mode === "initial" ? "¡Marca generada!" : "¡Marca actualizada!");
                setTimeout(() => { resetForm(); onOpenChange(false); onSuccess(); }, 800);
                return;
            }
            if (status.status === "failed") {
                setErrorState({ type: "generic", message: status.error || "Error desconocido" });
                setIsProcessing(false);
                return;
            }
        } catch (err) {
            // Network error on poll — retry, don't fail (backend may still be working)
            console.warn("[SmartFill] Poll error, retrying:", err);
        }

        pollTimerRef.current = setTimeout(poll, 3000);
    };

    pollTimerRef.current = setTimeout(poll, 1000); // first poll after 1s
};
```

**Removals:**
- Remove the fake `progressInterval` with `setInterval` (lines 83-89)
- Remove the hardcoded `setTimeout` stage messages (lines 92-97)
- Remove the `"Failed to fetch"` → timeout heuristic detection (lines 141)
- Remove the `"timeout"` error type entirely — no longer needed

## Files Changed (6 total)

| File | Action | Description |
|---|---|---|
| `backend/src/modules/brand/workers/tasks.py` | **New** | ARQ task `run_brand_extraction` with Redis progress |
| `backend/src/modules/brand/api/extraction.py` | **Modify** | POST returns 202 + job_id; new GET /status endpoint |
| `backend/src/modules/brand/application/extraction_service.py` | **Modify** | Add optional `progress_callback` to `extract_all()` |
| `backend/src/modules/copilot/application/services/brand_ai_actions_service.py` | **Modify** | Forward `progress_callback` param to `extract_all()` |
| `backend/src/modules/analytics/workers/settings.py` | **Modify** | Register `run_brand_extraction` in functions list |
| `backend/src/main.py` | **Modify** | Shared ARQ pool on startup/shutdown |
| `frontend/src/lib/api/ai-actions.ts` | **Modify** | Replace sync fetch with POST + poll |
| `frontend/src/features/brand/components/smart-fill/smart-fill-dialog.tsx` | **Modify** | Real progress from polling, cleanup on unmount |

## Edge Cases

1. **User closes dialog mid-extraction:** `useEffect` cleanup clears the poll timer and nullifies `activeJobRef`. Job continues in worker, data saves to DB. Next time user opens Brand Studio, data is there.
2. **User starts second extraction while first is running:** Each gets a unique `job_id`. `activeJobRef` switches to the new one, old polls stop (stale check). Old job completes silently (idempotent save).
3. **Worker crashes mid-job:** Redis key retains last progress with `started_at`. Status endpoint detects stale jobs (>10 min processing) and returns `failed`. Frontend shows error with retry option.
4. **Redis unavailable:** POST endpoint returns 503 immediately. User sees "Servicio temporalmente no disponible".
5. **Poll network error:** Individual poll failures are caught and retried silently. The job keeps running server-side regardless.

## What Does NOT Change

- `BrandExtractionService` internals (waves, profiles, AI calls) — untouched except adding optional callback
- `GET /brand/settings` — the source of truth for loading brand data after completion
- Database schema — no migrations needed
- The `/extract` endpoint (single-field extraction) — unrelated, unchanged

## Testing

- **Backend:** Test POST returns 202 + job_id; test GET /status reads Redis correctly; test task writes progress through each wave and completes; test stale detection at >10 min
- **Frontend:** Test polling loop starts after POST, updates progress, stops on completed/failed, cleans up on unmount
- **Integration:** Full flow in dev Docker — worker must be running: `docker compose --profile extended up -d`
