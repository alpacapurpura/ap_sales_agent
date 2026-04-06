# Protocolo de Seguridad Paralela (OBLIGATORIO)

Chris trabaja con 1 instancia de Claude Code en una sola máquina (WSL).
Este protocolo es BLOQUEANTE — debe ejecutarse antes de cualquier otra acción.

## Al INICIAR cualquier conversación

ANTES de leer código, hacer planes, o ejecutar cualquier herramienta, ejecutar:

    git status --short && git stash list && git branch --show-current && git log --oneline -3

### Árbol de decisión:

1. **Working tree limpio + en `main`** → Proceder. Crear feature branch para trabajo nuevo.
2. **Working tree limpio + en feature branch** → Preguntar: "Estoy en rama `X`. ¿Continúo aquí o vuelvo a main?"
3. **Working tree SUCIO (cambios sin commitear)** → PARAR. Ejecutar protocolo de rescate:
   - Informar: "Encontré N archivos modificados sin commitear de una sesión anterior: [lista]"
   - Ofrecer: A) Rescatar en branch (`/rescata`), B) Commitear directamente, C) Descartar (solo si Chris lo pide explícitamente)
   - NUNCA empezar trabajo nuevo hasta que el working tree esté limpio

## Regla de feature branches

- Cada tarea significativa (>2 archivos o >10 líneas) va en su propia rama
- Naming: `feature/`, `fix/`, `refactor/`, `chore/` + `<scope>-<descripcion>`
- Solo hotfixes triviales (typos, 1 línea) van directo en `main`

## Sub-agentes paralelos (CRÍTICO)

Cuando se lanzan múltiples agentes (subagent_type) que van a ESCRIBIR código:

### OBLIGATORIO: usar `isolation: "worktree"`
- Cada agente que escribe código DEBE usar `isolation: "worktree"` para obtener su propia copia aislada del repo
- NUNCA lanzar múltiples agentes que escriben en el MISMO directorio — causa corrupción de archivos y conflictos de git checkout
- Agentes de solo lectura (Explore, Plan) NO necesitan worktree

### Flujo correcto:
1. Lanzar agentes con `isolation: "worktree"` → cada uno trabaja en `/tmp/.../worktree-xxx/`
2. Cada agente commitea en su worktree
3. Al terminar, mergear cada worktree al branch principal
4. Los worktrees sin cambios se limpian automáticamente

### PROHIBIDO:
- Lanzar 2+ agentes que escriben código sin `isolation: "worktree"`
- Que un sub-agente haga `git checkout` en el directorio principal
- Que un sub-agente cree un branch en el directorio principal mientras otro escribe

### Excepciones (agentes sin worktree):
- Agentes que SOLO leen (Explore, research) → OK sin worktree
- Un SOLO agente escribiendo a la vez → OK sin worktree
- Agentes que editan archivos completamente distintos Y no tocan git → riesgoso pero tolerable

## Al CERRAR cualquier conversación

Cuando Chris dice "eso es todo", "gracias", "ya", "cierra", o indica que terminó:

1. `git status --short`
2. Si hay cambios → commitear con mensaje convencional, reportar hash
3. Si hay stashes creados en esta sesión → reportar
4. Mensaje final obligatorio: "Working tree LIMPIO en rama `X`. Seguro cerrar."

Si hay trabajo WIP que no compila: crear stash con mensaje descriptivo (`git stash push -m "WIP: descripción"`)

## Antes de merge a main

1. Commitear TODO lo pendiente en la feature branch
2. `git checkout main && git pull origin main`
3. `git checkout <feature-branch> && git rebase main`
4. Resolver conflictos si los hay
5. Ejecutar tests relevantes (lint + pytest o vitest según el scope)
6. Merge: `git checkout main && git merge <feature-branch>`
7. Eliminar la rama local: `git branch -d <feature-branch>`

## PROHIBIDO

- Empezar a escribir código con working tree sucio de otra sesión
- Hacer `git checkout` a otra rama con cambios uncommitted (se pierden)
- Cerrar conversación sin commitear o reportar estado limpio
- Trabajar en `main` directamente para cambios significativos
- Lanzar múltiples agentes escritores sin worktree isolation
