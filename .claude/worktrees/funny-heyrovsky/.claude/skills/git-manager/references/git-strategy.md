# Git Strategy — Nicolify

## Branch Model

```
main (producción)
  └── feature/audit-module-frontend
  └── feature/shopify-integration
  └── fix/telegram-typing-indicator
  └── refactor/semantic-router-tenant-aware
  └── chore/update-dependencies
```

- **main** = siempre deployable a producción
- Nunca se trabaja directo en `main`
- Cada feature/fix tiene su propia rama
- Las ramas se mergean vía PR (o merge directo si el equipo es solo el founder)

## Convención de Commits (Conventional Commits)

```
<type>(<scope>): <descripcion en minúsculas>

[cuerpo opcional - qué y por qué, no el cómo]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

### Tipos válidos
| Tipo | Cuándo usarlo |
|------|---------------|
| `feat` | Nueva funcionalidad visible para el usuario |
| `fix` | Corrección de bug |
| `refactor` | Cambio de código sin cambiar comportamiento externo |
| `perf` | Mejora de rendimiento |
| `docs` | Solo documentación |
| `chore` | Config, deps, CI, build |
| `test` | Tests |
| `style` | Formato, whitespace (sin cambio de lógica) |

### Scopes comunes del proyecto
- `sales-agent`, `audit`, `brand`, `offer`, `crm`, `connections`
- `backend`, `frontend`, `infra`, `db`, `auth`

### Ejemplos
```
feat(audit): add llm_summary to timeline trace events
fix(telegram): keep typing indicator alive during long LLM processing
refactor(semantic-router): make intent detection tenant-aware
chore(docker): add restart policy to production compose
docs(sales-agent): document AKS knowledge builder flow
```

## Semver — Cuándo incrementar qué

### Patch (X.X.→1)
- Bug fixes
- Mejoras de rendimiento
- Cambios internos que no afectan el contrato de API
- Actualizaciones de prompts/templates del agente

### Minor (X.→1.0)
- Nueva funcionalidad visible para el usuario final
- Nuevos endpoints de API (sin romper los existentes)
- Nuevos módulos o integraciones
- Cambios de UX significativos

### Major (→1.0.0)
- Breaking changes en la API
- Cambio de arquitectura fundamental
- Nueva plataforma/canal de ventas soportado
- Cambio en el modelo de datos que requiere migración manual

## Workflow Diagram

```
1. git checkout main && git pull
2. git checkout -b feature/mi-feature
3. [desarrollar, commits frecuentes]
4. git fetch origin && git rebase origin/main
5. git push origin feature/mi-feature
6. gh pr create (o merge directo si es solo el founder)
7. [review / merge]
8. git checkout main && git pull
9. [si es release] git tag -a vX.X.X && git push origin vX.X.X
10. gh release create vX.X.X
```

## Docker Deploy a Producción

Después de mergear a `main` y crear el release tag:

```bash
# En el servidor de producción
git pull origin main
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker exec -it visionarias_brain_prod alembic upgrade head  # si hay migraciones
```
