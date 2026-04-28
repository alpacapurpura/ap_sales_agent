---
name: pase-produccion
description: >
  Full production deployment pipeline: merge development to main, run /test-all fixing all errors,
  commit, push to trigger GitHub Actions, and monitor the workflow until deployment completes.
  Use when the user says "pase a producción", "hagamos un pase", "deploy to production",
  "pasamos a prod", "subamos a producción", or "vamos a producción".
version: 1.0.0
---

# Pase a Producción — Pipeline Completo

Eres el orquestador de deploys de Nicolify. Tu objetivo es llevar el código desde ramas dispersas
hasta producción con cero intervención manual, verificando calidad en cada paso.

## Parámetros Opcionales

El usuario puede decir:
- "pase a producción **solo main**" → skip merge phase, solo test+push
- "pase a producción **dry-run**" → ejecutar todo excepto el push final

---

## Fase 1: Reconnaissance (Estado Actual)

Antes de tocar nada, entender el estado completo:

```bash
git status
git branch -a
git log --oneline -10
git stash list
```

**Verificar:**
- ¿Hay cambios sin commitear en la rama actual? → Commitear o stashear primero
- ¿Hay ramas remotas que no existen localmente? → `git fetch --prune origin`
- ¿Cuáles ramas tienen commits por delante de main?

**Reportar al usuario:**
> "Encontré X ramas con cambios pendientes: [lista]. ¿Procedo a mergear todas a main, o excluyo alguna?"

Si el usuario ya indicó exclusiones, proceder sin preguntar.

---

## Fase 2: Consolidación (Merge development → Main)

### 2.1 Preparar main
```bash
git checkout main
git pull origin main
```

### 2.2 Merge development
```bash
git merge development
```

**Si hay conflictos:**
1. Intentar resolver automáticamente (priorizar development para código nuevo, main para infra)
2. Si es ambiguo → preguntar al usuario mostrando el diff conflictivo

### 2.3 Verificar:
```bash
git log --oneline -20  # verificar que todos los commits están en main
```

**NO pushear todavía.** Primero pasar las pruebas.

---

## Fase 2.5: E2E Smoke (Nativo en WSL)

**Objetivo:** Correr la suite smoke de Playwright localmente antes de pushear a main.
Se ejecuta NATIVAMENTE en WSL (no Docker — Docker crashea la laptop).

### 2.5.1 Requisitos
- Dev containers corriendo: `docker compose up -d`
- `.env` en la raíz del repo con credenciales Clerk E2E

### 2.5.2 Ejecutar E2E Smoke
```bash
cd frontend && npx playwright test --project=smoke
```

Esto corre 32 smoke tests en ~2 minutos. `playwright.config.ts` carga `.env` automáticamente.

### 2.5.3 Resultados posibles:

**SUCCESS (32 passed):** Continuar con Fase 3 (verificación local lint+tests).

**FAILURE:**
1. Leer los `error-context.md` en `frontend/test-results/*/`
2. Si es "Password is incorrect": sincronizar password en Clerk Dashboard con `E2E_CLERK_USER_PASSWORD` del `.env`
3. Si es "strict mode violation": agregar `.first()` al locator del POM
4. Si es "element not found": verificar que el mock de la fixture devuelve los datos esperados
5. Si `test-results/` tiene permisos root: `docker run --rm -v $PWD/frontend:/f alpine sh -c 'rm -rf /f/test-results/'`
6. Máximo 3 intentos de fix. Si falla 3 veces → reportar al usuario.

**NOTA:** Si el usuario pide "pase rápido" o indica urgencia, se puede saltar esta fase.
E2E NO es parte del pase a producción real (push a main) — es validación extra.

---

## Fase 3: Verificación Completa

Esta fase se divide en dos sub-fases. **Las dos son blocker antes del
push**. Saltarse 3b porque "el nativo pasó" reproduce el ciclo de 5
deploys fallidos del 2026-04-27 (env vars, TZ=UTC, Node heap, dockerignore).

### Fase 3a: `/test-all` nativo (rápido, ~30-60s)

Invocar el skill `/test-all` completo. Esto ejecuta:
1. Backend lint (ruff)
2. Backend format check
3. Architecture fitness tests
4. Backend tests + coverage (pytest)
5. Frontend types (tsc)
6. Frontend lint (ESLint)
7. Frontend tests + coverage (vitest)
8. Health checks (jscpd, knip, madge, audits)
9. Migration verification (fresh DB)

### Fase 3b: CI Parity Docker (BLOCKER, ~2-8 min)

Invocar el script que replica el job ``quality-gates`` del workflow CI:
```bash
bash scripts/ci-parity.sh
# or:
make ci-parity
```

Construye las MISMAS imágenes Docker que CI (``target=test`` de
``backend/Dockerfile`` y ``frontend/Dockerfile``) y corre las mismas
verificaciones con ``TZ=UTC`` y ``NODE_OPTIONS=--max-old-space-size=4096``.

**Por qué este gate es no-negociable** (resumido — full table en
``/test-all.md`` Step 12):

| Diferencia | Falla histórica |
|---|---|
| ``backend/.env.test`` ≠ ``backend/.env`` | Kimi K2 temperature clamp tests |
| TZ=UTC vs host UTC-3..-5 | Lima locale period window |
| Node heap ~1GB en container | ``tsc --noEmit`` OOM SIGABRT |
| ``.dockerignore`` excluye ``data/`` | ``test_seed_marketing_kb`` FileNotFoundError |

Si `ci-parity` falla pero `/test-all` nativo pasó: el problema es el
ambiente CI, NO el código. Investigar y arreglar antes del push (no
empujar y arreglar en CI loop).

### Protocolo de corrección de errores:

**Para cada error encontrado en 3a o 3b:**
1. Leer el error completo y entender la causa raíz
2. Corregir el código (NUNCA skipear tests ni desactivar lint rules)
3. Re-ejecutar SOLO el step que falló para verificar
4. Si falló en 3b pero no en 3a: el fix probablemente es env/TZ/heap/
   dockerignore — no toques tests-que-pasaron-localmente.

**Orden de prioridad de fixes:**
1. Errores de compilación/tipos (bloquean todo)
2. Errores de lint (ruff/eslint)
3. Tests que fallan
4. Coverage insuficiente (solo si está bajo el threshold)

**Si un fix en un módulo rompe otro módulo:**
- STOP. Analizar el impacto cruzado.
- Preguntar al usuario si es un cambio de scope esperado.

### Iteración:
Repetir 3a + 3b hasta que TODOS los steps pasen. Máximo 3 iteraciones
completas. Si después de 3 iteraciones aún falla, reportar los errores
restantes y pedir dirección.

---

## Fase 4: Commit & Push

Una vez que `/test-all` pasa completamente:

### 4.1 Stage y commit de fixes
```bash
git add <archivos-modificados>  # NUNCA git add . sin revisar
git commit -m "chore(ci): fix all CI errors for production deploy

- [lista de fixes aplicados]

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

### 4.2 Push a main
```bash
git push origin main
```

**IMPORTANTE:** Este push activa el GitHub Actions pipeline (`deploy-prod.yml`).

---

## Fase 5: Monitoreo de GitHub Actions

Inmediatamente después del push, iniciar monitoreo:

### 5.1 Obtener el workflow run
```bash
gh run list --branch main --limit 1 --json databaseId,status,conclusion,name,createdAt
```

### 5.2 Polling loop
Cada ~30 segundos, verificar el estado:

```bash
gh run view <run-id> --json status,conclusion,jobs
```

**Reportar al usuario en cada check:**
- Status actual del run (queued / in_progress / completed)
- Jobs individuales y su estado
- Tiempo transcurrido

### 5.3 Resultados posibles:

**SUCCESS:**
> "Deploy completado exitosamente en X minutos. Pipeline: quality-gates PASS → security-scan PASS → push images PASS.
> Imágenes publicadas: `ghcr.io/alpacapurpura/visionarias-backend:latest` y `ghcr.io/alpacapurpura/visionarias-frontend:latest`"

**FAILURE:**
> "Deploy FALLÓ en el job [nombre]. Error: [detalle].
> ¿Quiero investigar y corregir? Si es un fix rápido, puedo hacerlo y re-pushear."

Si falla, ofrecer investigar los logs:
```bash
gh run view <run-id> --log-failed
```

---

## Fase 6: Limpieza Post-Deploy

Solo después de un deploy exitoso:

### 6.1 Sincronizar development con main
```bash
git checkout development
git merge main
```

### 6.2 Reporte final
```
## Pase a Producción — Resumen

| Fase | Resultado |
|---|---|
| Ramas mergeadas | X de Y |
| CI fixes aplicados | N archivos modificados |
| /test-all | PASS (X iteraciones) |
| GitHub Actions | SUCCESS (Xm Xs) |
| Ramas limpiadas | X eliminadas |

Deploy ID: <run-id>
Imágenes: ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest
```

---

## Reglas de Seguridad

- **NUNCA** hacer `git push --force` a main
- **NUNCA** skipear tests o desactivar lint rules para "pasar" CI
- **NUNCA** mergear sin verificar primero que no hay conflictos
- **NUNCA** borrar ramas sin confirmación del usuario
- **SIEMPRE** preguntar antes de resolver conflictos ambiguos
- **SIEMPRE** verificar que el push activó el workflow correcto
- Si algo sale mal, el rollback es: `git revert HEAD` + push (NUNCA force push)
