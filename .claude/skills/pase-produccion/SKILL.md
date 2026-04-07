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

## Fase 3: Verificación Completa (/test-all)

Invocar el skill `/test-all` completo. Esto ejecuta:
1. Backend lint (ruff)
2. Backend tests + coverage (pytest)
3. Frontend types (tsc)
4. Frontend lint (ESLint)
5. Frontend tests + coverage (vitest)
6. E2E Smoke (Playwright)
7. Migration verification (fresh DB)

### Protocolo de corrección de errores:

**Para cada error encontrado:**
1. Leer el error completo y entender la causa raíz
2. Corregir el código (NUNCA skipear tests ni desactivar lint rules)
3. Re-ejecutar SOLO el step que falló para verificar
4. Continuar con el siguiente step

**Orden de prioridad de fixes:**
1. Errores de compilación/tipos (bloquean todo)
2. Errores de lint (ruff/eslint)
3. Tests que fallan
4. Coverage insuficiente (solo si está bajo el threshold)

**Si un fix en un módulo rompe otro módulo:**
- STOP. Analizar el impacto cruzado.
- Preguntar al usuario si es un cambio de scope esperado.

### Iteración:
Repetir `/test-all` hasta que TODOS los steps pasen. Máximo 3 iteraciones completas.
Si después de 3 iteraciones aún falla, reportar los errores restantes y pedir dirección.

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
