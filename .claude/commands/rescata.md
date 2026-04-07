Rescatar cambios huérfanos de una sesión anterior de Claude Code.

1. Ejecutar: `git status --short && git diff --stat`
2. Mostrar al usuario qué archivos están modificados y un resumen de los cambios
3. Asegurarse de estar en `development`: `git checkout development` (crear si no existe: `git checkout -b development`)
4. Stage archivos (NUNCA .env ni secrets): `git add` de cada archivo individualmente, revisando
5. Commit: mensaje convencional describiendo los cambios rescatados
6. Reportar: "Cambios rescatados en `development`. Working tree LIMPIO."
