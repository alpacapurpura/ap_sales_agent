Protocolo de cierre limpio. Garantizar que no quedan cambios sin commitear.

1. Ejecutar: `git status --short && git branch --show-current`
2. Si hay cambios sin commitear:
   a. Mostrar `git diff --stat`
   b. Stage archivos relevantes (revisando individualmente, nunca .env)
   c. Commit con mensaje convencional apropiado
   d. Push si hay rama remota configurada
3. Si NO hay cambios: reportar que ya está limpio
4. Mensaje final obligatorio: "Working tree LIMPIO en rama `<branch>`. Commit: <hash> <mensaje>. Seguro cerrar."
