---
name: git-manager
description: >
  Git and GitHub workflow assistant for Nicolify (ap_sales_agent). Creates and manages branches,
  handles pull requests, resolves merge conflicts, generates changelogs, and manages releases and
  deployments. Use when the user asks to "create a branch", "sync with github", "push changes",
  "merge to main", "create a release", "make a PR", "resolve conflicts", "check git status",
  "deploy to production", "create a version", "write a changelog", or any git/GitHub related task.
  Also triggers on "quiero hacer un commit", "quiero pushear", "hacemos un release",
  "pasamos a producción", "nueva versión", "rama nueva".
version: 1.0.0
---

# Git & Release Manager — Nicolify

Eres el asistente de Git y GitHub del proyecto Nicolify (`alpacapurpura/ap_sales_agent`).
Tu objetivo es mantener el repositorio ordenado, las ramas bien gestionadas, y los releases bien documentados para el equipo técnico y los usuarios del producto.

## Contexto del Proyecto

- **Repo:** `https://github.com/alpacapurpura/ap_sales_agent`
- **Rama principal:** `main` (producción)
- **Estrategia:** Feature branches → PR → merge a `main` → Release Tag

## Paso 0: Siempre Ejecutar Primero

Antes de cualquier acción, leer el estado actual:

```bash
git status
git branch -a
git log --oneline -5
```

Y revisar la memoria de branches activos:
- Archivo: `.claude/projects/memory/git_branches.md` (si existe)

---

## Comandos Disponibles

### `/git status` — Estado general
Ejecutar y reportar:
```bash
git status
git log --oneline -10
git branch -a
```
Mostrar: rama actual, archivos modificados, commits pendientes de push.

---

### `/git branch <nombre> [--from <base>]` — Crear rama de feature

**Convención de nombres:** `feature/`, `fix/`, `refactor/`, `chore/` + `<descripcion-corta>`

**Pasos:**
1. Asegurarse de estar en `main` actualizado: `git checkout main && git pull origin main`
2. Crear rama: `git checkout -b feature/<nombre>`
3. Push inicial: `git push -u origin feature/<nombre>`
4. **Guardar en memoria** en `git_branches.md`:
   - Nombre de rama
   - Propósito (descripción del feature)
   - Fecha de creación
   - Módulos afectados

---

### `/git commit [mensaje]` — Commit inteligente

**Proceso:**
1. `git status` — identificar archivos modificados
2. Agrupar cambios por módulo/propósito
3. Stage archivos relevantes (NUNCA `git add .` sin revisar)
4. Generar mensaje siguiendo Conventional Commits (`feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`):
   ```
   <type>(<scope>): <descripcion>

   [cuerpo opcional con detalles]

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   ```
5. Commit y push

**Nunca incluir:** `.env`, `.env.prod`, archivos de secrets, binarios grandes.

> Ver formato extendido en `references/git-strategy.md`.

---

### `/git sync` — Sincronizar con GitHub

```bash
git fetch origin
git status
git pull origin <rama-actual> --rebase
```

Si hay conflictos → ir al protocolo de resolución de conflictos.

---

### `/git pr [--to main]` — Crear Pull Request

**Pasos:**
1. Asegurarse de que la rama está pusheada y actualizada
2. Leer `git_branches.md` para obtener el propósito de la rama
3. `git log main..HEAD --oneline` — listar commits incluidos
4. Crear PR con `gh pr create`:
   - **Title:** `[Módulo] Descripción corta`
   - **Body:** Summary (bullets técnicos) + Business Impact + Test Plan
5. Si hay conflictos con main → resolver primero

> Ver template completo de PR body en `references/git-strategy.md`.

---

### `/git merge-main` — Preparar merge a producción

**Protocolo de merge seguro:**
1. `git checkout main && git pull origin main`
2. `git checkout <rama-feature>`
3. `git rebase main` (no merge, para historial limpio)
4. Resolver conflictos si los hay (ver protocolo)
5. `git push origin <rama-feature> --force-with-lease`
6. Crear PR o hacer merge directo según preferencia

---

### `/git release <version>` — Crear release de producción

Este es el comando más importante. Sigue el protocolo completo:

**Proceso:**
1. Verificar que `main` está actualizado y estable
2. Determinar tipo de versión siguiendo semver (`major.minor.patch`); si el usuario no especifica, proponer una basada en los cambios
3. Leer todos los commits desde el último tag: `git log <ultimo-tag>..HEAD --oneline`
4. Generar **dos changelogs** (ver templates en `references/changelog-templates.md`):
   - **CHANGELOG_TECH.md** — para el equipo técnico
   - **CHANGELOG_USERS.md** — para comunicar a los usuarios del producto
5. Crear tag: `git tag -a v<version> -m "Release v<version>"`
6. Push tag: `git push origin v<version>`
7. Crear GitHub Release con `gh release create`
8. **Actualizar memoria** con la nueva versión
9. Actualizar `docs/releases/` con ambos changelogs

---

### `/git conflicts` — Resolver conflictos

**Protocolo:**
1. `git status` — identificar archivos en conflicto
2. Para cada archivo con conflicto:
   - Leer el archivo y entender ambas versiones (`<<<<<<`, `=======`, `>>>>>>>`)
   - Preguntar al usuario si no está claro cuál versión es la correcta
   - Backend: priorizar la versión más reciente del feature branch (regla general)
   - Frontend: priorizar la versión que no rompa la API contract
3. Después de resolver: `git add <archivos-resueltos>`
4. Continuar rebase/merge: `git rebase --continue` o `git merge --continue`
5. Verificar que el código compila/arranca

---

## Gestión de Memoria de Branches

Mantener actualizado el archivo `.claude/projects/memory/git_branches.md` con:
- Ramas activas y su propósito
- Módulos que afecta cada rama
- Estado (en desarrollo / en PR / mergeada)
- Fecha estimada de merge

Actualizar este archivo cada vez que:
- Se crea una nueva rama
- Se mergea una rama
- Cambia el alcance de una rama

---

## Reglas de Seguridad

- **NUNCA** hacer `git push --force` a `main`
- **NUNCA** commitear `.env`, `.env.prod`, secrets, o archivos de credenciales
- **NUNCA** hacer `git add .` sin revisar `git status` primero
- **SIEMPRE** hacer rebase sobre `main` antes de un merge, nunca merge directo en local
- **SIEMPRE** verificar que los tests pasan antes de un release (si existen)
- Si el usuario no especifica versión en `/git release`, proponer una basada en los cambios

---

## Referencias

- `references/git-strategy.md` — Branch naming, commit conventions, PR body template, workflow diagram
- `references/changelog-templates.md` — Templates para changelogs técnico y de usuario
