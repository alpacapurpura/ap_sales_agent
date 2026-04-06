# Mejoras de Proceso — To Do

Hallazgos detectados por Claude Code durante ejecución. Revisar y resolver.

## Lecciones del Pase a Producción 2026-04-06

### 1. /test-all NO valida migraciones contra BD fresca en CI
- **Problema:** `/test-all` local ejecuta `alembic upgrade head` contra la BD existente (que ya tiene todas las tablas). Las migraciones no-idempotentes pasan porque las tablas ya existen. En CI (BD limpia) fallan.
- **Fix aplicado:** Arregladas migraciones 028, 030, 034, 036 con guards `DO $$ IF EXISTS`.
- [ ] Agregar step en `/test-all` que corra migraciones contra BD fresca (ya existe como step 11 pero no detectó estos errores porque localmente el backend container monta el código actual, no el código commiteado)
- [ ] Crear arch fitness test: escanear migraciones buscando `ALTER TABLE X` sin guard `IF EXISTS(table)` para tablas que no son creadas por migraciones (appointments, messages, agent_state_checkpoints, conversations, channel_connections)

### 2. E2E en CI necesitaba env vars no documentados
- **Problema:** El backend `Settings` requiere 12+ env vars obligatorias (LOG_LEVEL, OPENAI_API_KEY, REDIS_URL, etc). El job E2E solo tenía las de frontend/auth.
- **Fix aplicado:** Agregados dummy values en el workflow.
- [ ] Crear `.env.ci.example` con TODOS los env vars necesarios para CI E2E, documentado y versionado
- [ ] Considerar hacer que Settings tenga defaults para env vars no-críticos en test mode

### 3. `docker compose --wait` no funciona con init containers + tunnel
- **Problema:** `--wait` espera que TODOS los servicios estén healthy. `init_cache` sale con code 0 (esperado) y `cloudflare-tunnel` con token `disabled` tarda 3+ min.
- **Fix aplicado:** Reemplazado con `up -d` + health check manual solo de los servicios necesarios.
- [ ] Considerar crear un `docker-compose.ci.yml` override que excluya tunnel e init_cache

### 4. Tests de arquitectura cross-stack no funcionan en Docker CI
- **Problema:** `test_currency_consistency.py` intentaba leer archivos frontend desde el container backend. En CI el backend corre aislado sin acceso al frontend.
- **Fix aplicado:** Removida dependencia cross-stack, validación solo del backend.
- [ ] Regla: los tests de arquitectura backend NUNCA deben depender de archivos frontend. Si se necesita validación cross-stack, hacerla como step separado nativo.

### 5. Sesiones paralelas de Claude Code pueden interferir
- **Problema:** La sesión paralela (currency-standardization) hizo commit a main con un test roto (`test_currency_consistency`) que rompió quality-gates del pase a producción.
- [ ] Regla: cada sesión de Claude Code DEBE trabajar en su propia feature branch. Solo mergear a main después de pasar /test-all en la feature branch.
- [ ] El protocolo paralelo actual no previene commits rotos de otras sesiones

### 6. E2E smoke local falla por OOM del Next.js container
- **Problema:** Container Next.js dev con 2048MB se cae bajo carga de Playwright (HMR + watchers + compilación + memoria).
- **Fix aplicado:** `shm_size: 2gb` + `--disable-dev-shm-usage` + target `e2e-native-smoke` (sin container Docker).
- [ ] A largo plazo: resolver el bug de `next build` para poder usar `next start` en E2E (3-5x menos memoria)
- [ ] Documentar en CLAUDE.md que E2E preferir `make e2e-native-smoke` sobre `make e2e-smoke` en laptops con poca RAM
