# Protocolo de Seguridad Paralela (OBLIGATORIO)

Chris trabaja con 2-3 instancias de Claude Code en paralelo sobre el mismo directorio.
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
- Cada instancia de Claude Code trabaja en SU propia rama

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
