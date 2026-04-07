# Protocolo de Seguridad Paralela (OBLIGATORIO)

Chris trabaja con múltiples instancias de Claude Code en una sola máquina (WSL).
Este protocolo es BLOQUEANTE — debe ejecutarse antes de cualquier otra acción.

## Modelo de Ramas (Simplificado)

```
main (producción — push = deploy automático)
  └── development (ÚNICA rama de trabajo — todos los agentes commitean aquí)
```

- **`development`** = rama de trabajo. TODO el desarrollo va aquí. Sin excepciones.
- **`main`** = producción. Solo recibe merges de `development` durante pase a producción.
- **NUNCA crear feature branches, worktrees, ni ramas adicionales** salvo que Chris lo pida explícitamente.

## Al INICIAR cualquier conversación

ANTES de leer código, hacer planes, o ejecutar cualquier herramienta, ejecutar:

    git status --short && git stash list && git branch --show-current && git log --oneline -3

### Árbol de decisión:

1. **En `development` + working tree limpio** → Proceder directamente.
2. **En `main` + working tree limpio** → `git checkout development` (crearla si no existe: `git checkout -b development`).
3. **En otra rama** → `git checkout development`. Si hay commits útiles en la otra rama, preguntar a Chris si mergearlos a development.
4. **Working tree SUCIO (cambios sin commitear)** → PARAR. Ejecutar protocolo de rescate:
   - Informar: "Encontré N archivos modificados sin commitear: [lista]"
   - Ofrecer: A) Commitear en `development`, B) Stash, C) Descartar (solo si Chris lo pide explícitamente)
   - NUNCA empezar trabajo nuevo hasta que el working tree esté limpio

## Sincronización main → development

Si `main` tiene commits que `development` no tiene (ej: otro agente mergeó directo):

```bash
git checkout development
git merge main
```

NUNCA al revés (development → main) excepto durante pase a producción.

## Multi-agente (múltiples instancias de Claude Code)

- Chris coordina qué módulo trabaja cada agente
- Cada agente commitea en `development` directamente
- **NO usar `isolation: "worktree"`** — causa más problemas que los que resuelve
- **NO crear branches** — un solo branch para todos
- Si dos agentes tocan el mismo archivo → responsabilidad de Chris coordinar
- Agentes de solo lectura (Explore, Plan) no necesitan precauciones especiales

## Al CERRAR cualquier conversación

Cuando Chris dice "eso es todo", "gracias", "ya", "cierra", o indica que terminó:

1. `git status --short`
2. Si hay cambios → commitear con mensaje convencional, reportar hash
3. Si hay stashes creados en esta sesión → reportar
4. Mensaje final obligatorio: "Working tree LIMPIO en rama `development`. Seguro cerrar."

Si hay trabajo WIP que no compila: crear stash con mensaje descriptivo (`git stash push -m "WIP: descripción"`)

## PROHIBIDO

- Crear feature branches (salvo instrucción explícita de Chris)
- Crear worktrees (salvo instrucción explícita de Chris)
- Hacer `git checkout` a ramas que no sean `development` o `main`
- Empezar a escribir código con working tree sucio de otra sesión
- Cerrar conversación sin commitear o reportar estado limpio
- Push a `origin main` sin aprobación explícita (= deploy a producción)
