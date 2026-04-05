Rescatar cambios huérfanos de una sesión anterior de Claude Code.

1. Ejecutar: `git status --short && git diff --stat`
2. Mostrar al usuario qué archivos están modificados y un resumen de los cambios
3. Crear rama de rescate: `git checkout -b rescue/$(date +%Y-%m-%d-%H%M%S)`
4. Stage archivos (NUNCA .env ni secrets): `git add` de cada archivo individualmente, revisando
5. Commit: mensaje convencional describiendo los cambios rescatados
6. Volver a main: `git checkout main`
7. Reportar: "Cambios rescatados en rama `rescue/YYYY-MM-DD-HHMMSS`. Working tree LIMPIO."
8. Preguntar: "¿Quieres que mergee estos cambios a main, o los dejamos en la rama de rescate por ahora?"
