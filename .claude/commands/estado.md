Diagnóstico rápido del estado del repositorio.

1. Ejecutar: `git status --short && echo "---" && git stash list && echo "---" && git branch --show-current && echo "---" && git log --oneline -5`
2. Ejecutar: `docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || echo "Docker no disponible"`
3. Reportar en formato:
   - Rama actual
   - Archivos modificados (si los hay)
   - Stashes pendientes (si los hay)
   - Últimos 5 commits
   - Estado de containers Docker
   - Veredicto: "LIMPIO - seguro trabajar" o "SUCIO - ejecutar /rescata primero"
