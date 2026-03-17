# Production Deployment Checklist

## 1. Pre-Deploy Checks

- [ ] **Compare services:** Diff `docker-compose.yml` vs `docker-compose.prod.yml` service names. Every dev service that should run in prod must exist in both files.
  ```bash
  diff <(grep -E '^\s+\w+:$' docker-compose.yml | sort) <(grep -E '^\s+\w+:$' docker-compose.prod.yml | sort)
  ```
- [ ] **Check new pip dependencies:** If any new packages were added to `requirements-runtime.txt`, verify they do not require CPU-specific instructions (AVX, SSE4.2, X86_V2). Common offenders: `numpy`, `scipy`, `torch`, `onnxruntime`, `faiss`.
- [ ] **Compare env vars:** Verify `.env.prod` has all variables present in `.env`. Missing vars cause silent failures.
  ```bash
  diff <(grep -oP '^[A-Z_]+' .env | sort) <(grep -oP '^[A-Z_]+' .env.prod | sort)
  ```
- [ ] **Validate compose syntax:**
  ```bash
  docker compose -f docker-compose.prod.yml config --quiet
  ```

## 2. Known Production Constraints

| Constraint | Detail |
|---|---|
| Server CPU | QEMU Virtual CPU version 2.5+ (supports SSE/SSE2 only) |
| Unsupported instructions | AVX, SSE4.2, X86_V2 -- any package requiring these will crash with `Illegal instruction` |
| numpy | Must stay pinned `<2.0` (2.0+ requires X86_V2). Pin must appear BEFORE `fastembed` in requirements. |
| ML/scientific libs | Any library shipping native wheels (ONNX, scipy, torch) must be tested on prod CPU arch before deploy. |

## 3. Post-Deploy Verification

```bash
# All services running
docker compose -f docker-compose.prod.yml ps

# Backend healthy
curl -f https://$API_DOMAIN/health

# Worker logs (should show "Started worker" or job processing)
docker logs visionarias_worker --tail 20

# Scheduler logs (should show cron registration)
docker logs visionarias_scheduler --tail 20

# Redis connectivity (check queued/completed jobs)
docker exec visionarias_redis redis-cli KEYS "arq:*"
```

## 4. Incident Log

| Date | Issue | Root Cause | Fix |
|---|---|---|---|
| 2026-03-17 | Backend failed to start (`Illegal instruction` crash) | numpy 2.x pulled by fastembed requires X86_V2 CPU instructions not available on QEMU | Pinned `numpy<2.0` in `requirements-runtime.txt` before fastembed |
| 2026-03-17 | Worker and scheduler not running in prod | Services existed in `docker-compose.yml` but were never added to `docker-compose.prod.yml` | Added both services to prod compose with same image/config |
