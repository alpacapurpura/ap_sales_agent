# Decisiones — PI-7-app-stability-restore

| # | Fecha | Decisión | Razón | PR |
|---|---|---|---|---|
| D-1 | 2026-05-01 | SPLIT scope PR-1 cross-surface en builder Sonnet (Bug #7) + PM ad-hoc (Bug #9) | Bug #9 root cause cambió mid-flight. Architect dijo WSL2 stale bind-mount; logs revelaron `LITELLM_ENVIRONMENT` missing + OOM. PM ad-hoc agile, builder no necesario para infra trivial | PR-1 |
| D-2 | 2026-05-01 | Bug #7 fix downstream EXTEND `PersonalityProfileDTO` existing | DTO ya tenía `from_attributes=True`. EXTEND vs LIFT-TO-SHARED. Anti-duplication satisfied. Fix mínimo (4 líneas + 1 import) | PR-1 |
| D-3 | 2026-05-01 | Bug #9 multi-causa fix: `LITELLM_ENVIRONMENT` propagation compose + memory 768M→1536M | 2 causas reales runtime: ValueError startup + OOM SIGKILL exit 137. Memory paridad con brain (1536M) safe sin sobre-provisioning | PR-1 |
| D-4 | 2026-05-01 | `cost_usd=0` aceptado como deuda separada NO bloqueante PI-7 | Métrica única éxito = `turn_end status='ok'`, no cost > 0. Pricing resolution falla provider mapping (deepseek tagged como openai) → backlog separado | PR-1 |
| D-5 | 2026-05-01 | Telegram Web typing inconsistente NO es bug nuestro | Backend dispara `sendChatAction` 11× HTTP 200 OK confirmed en logs. Cliente Telegram Web bug conocido vs apps nativas | PR-1 |
