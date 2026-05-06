# Learnings — S1-cascade-bugs-fix (PI-7)

## Process

| # | Learning | Severidad | Acción |
|---|---|---|---|
| L-1 | **Architect Opus puede missear root causes infra cuando solo usa `docker inspect`.** Architect propuso "WSL2 stale bind-mount" para Bug #9 sin correr `docker logs <container>` ni `docker events`. Logs runtime revelaron causas REALES (ValueError + OOM). | HIGH | Architect prompt template debe forzar `docker logs <container> | head -100` + `docker events --since 5m` cuando container exited. Ya cubierto en `01-architect-start.md` BLOQUE VARIABLE (línea "Comandos diagnose Bug #9 OBLIGATORIOS") — pero architect interpretó como diagnose superficial. **Fix template:** explicitar "HARD REQUIREMENT — citá output verbatim en CONTRACT § 7" |
| L-2 | **CONTEXT-BRIEF.md (Haiku) puede dar partial faithfulness scan.** Brief flagged `partial` (3 gaps non-blocking). Architect downstream basó decisión Bug #9 en brief sin re-running greps. | MED | Cuando Haiku flagea `partial` faithfulness, architect prompt MUST re-run scan él mismo (ya está en BLOQUE FIJO Path B). Reforzar en `01-architect-start.md` template |
| L-3 | **PR cross-surface single vs split: SPLIT correcto cuando cambia naturaleza.** Bug #7 = code + tests = builder. Bug #9 = restart + .env edits = PM ad-hoc no requiere CONTRACT formal. Split mid-flight evitó overhead builder para infra trivial | INFO | PR sizing decision: si una surface NO requiere code, NO requiere builder ni CONTRACT formal. PM ad-hoc OK. Documentar en `references/04-prd-template.md` |
| L-4 | **`docker-compose.yml environment:` propaga EXPLICITAMENTE.** Var en `.env` no llega al container si NO listada en `environment:` del service. Cause común de "edité .env y no funciona". | HIGH | Doc en `.claude/rules/debugging.md` o `references/`: "verificar `environment:` del service en compose antes de asumir `.env` es leído" |
| L-5 | **OOM exit code 137 silent en logs app.** Workers child mueren sin Python traceback porque kernel SIGKILL es brutal. Solo `docker events` + `docker inspect .State` revelan ExitCode=137. | INFO | Doc en `.claude/rules/debugging.md`: "Container `Up` con workers que mueren → check `docker events --filter container=X | grep die` para exit code real" |
| L-6 | **Memory paridad cross-services es heurística válida default.** Si servicio análogo (brain) corre 1536M sin OOM, replicar en peer (litellm) elimina guessing | INFO | Pattern aplicable a todos resource limits docker-compose |

## Smoke Chris-mediated

| # | Learning | Acción |
|---|---|---|
| L-7 | **Smoke real Chris-mediated > synthetic test post-fix.** Bot turn real validó pipeline completo (webhook → buffer → debounce → typing → semantic → LLM → response → trace persist). Synthetic unit test no detectaría OOM en LiteLLM ni memoria insuficiente | KEEP — patrón estándar PRs que tocan sales_agent/copilot |
| L-8 | **Telegram Web typing indicator NO es señal confiable de pipeline functional.** Cliente bug independiente. Verificar SIEMPRE en DB (`sales_agent_trace_event`) o app móvil/desktop antes diagnosticar bug typing | INFO |

## Cascade discovery pattern

| # | Learning | Acción |
|---|---|---|
| L-9 | **Cuando observability emerge (PR-2 PI-1.1), suele revelar bugs ocultos pre-existentes** (Bug #7 + #9 estuvieron silentes hasta traces persistentes). PI-7 fue handoff directo de PI-1.1 retro | INFO — patrón confirmado: post-observability mejora, smoke profundo descubre cascade |
