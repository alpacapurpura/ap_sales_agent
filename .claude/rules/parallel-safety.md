# Protocolo Seguridad Paralela (OBLIGATORIO)

Chris multi-instancias Claude Code en WSL. BLOQUEANTE — ejecutar antes cualquier acción.

## Modelo Ramas

```
main (prod — push = deploy auto)
  └── development (ÚNICA rama trabajo — todos commitean aquí)
```

- `development` = rama trabajo. TODO desarrollo. Sin excepciones.
- `main` = prod. Solo merges desde development en pase.
- **NUNCA feature branches/worktrees/ramas extra** salvo instrucción explícita.

## Al INICIAR conversación

ANTES leer código/planear/ejecutar tools:

    git status --short && git stash list && git branch --show-current && git log --oneline -3

### Decisión:

1. `development` + tree limpio → proceder.
2. `main` + limpio → `git checkout development` (crear si no existe).
3. Otra rama → `git checkout development`. Si commits útiles en otra, preguntar merge.
4. Tree SUCIO → PARAR:
   - Informar: "N archivos sin commit: [lista]"
   - Ofrecer: A) Commit en development, B) Stash, C) Descartar (solo si Chris pide)
   - NUNCA start nuevo hasta limpio

## Sync main → development

Si main tiene commits que development no:

```bash
git checkout development
git merge main
```

NUNCA reverse (dev→main) excepto pase prod.

## Multi-agente

- Chris coordina módulo per agente
- Cada agente commitea en development
- **NO `isolation: "worktree"`** — más problemas que soluciones
- **NO branches** — un branch para todos
- 2 agentes mismo archivo → Chris coordina
- Read-only agents (Explore, Plan): sin precauciones

### Scope commits (CRÍTICO paralelo)

Commit **ÚNICAMENTE archivos esta sesión modificó**. Otras sesiones pueden tener WIP.

- Stage por nombre: `git add path/file1 path/file2`
- **PROHIBIDO:** `git add .`, `git add -A`, `git add -u`
- Si status muestra archivos no tocados → dejar intactos, reportar al final
- Excepción única: Chris dice "commitea todo"

## Al CERRAR conversación

Chris dice "eso es todo", "gracias", "ya", "cierra":

1. `git status --short`
2. Cambios propios → stage por nombre, commit convencional, reportar hash
3. Archivos ajenos → dejar intactos, reportar
4. Stashes creados esta sesión → reportar
5. Mensaje final: "Archivos propios commiteados en `development`. Seguro cerrar."

WIP que no compila: `git stash push -m "WIP: descripción"`

## PROHIBIDO

- Crear feature branches (salvo instrucción Chris)
- Crear worktrees (salvo instrucción Chris)
- `git checkout` a ramas != development/main
- Empezar con tree sucio otra sesión
- Cerrar sin commit/reportar limpio
- Push `origin main` sin aprobación = deploy prod
