# Git Strategy — Nicolify

## Branch Model

```
main (producción — push = deploy automático via GitHub Actions)
  └── development (ÚNICA rama de trabajo — todos los agentes commitean aquí)
```

- **`main`** = siempre deployable a producción. Push a origin main = deploy automático.
- **`development`** = rama de trabajo. TODO el desarrollo va aquí.
- **NUNCA se crean feature branches, worktrees, ni ramas adicionales** salvo instrucción explícita de Chris.
- Merge `development` → `main` solo durante pase a producción.

## Convención de Commits (Conventional Commits)

```
<type>(<scope>): <descripcion en minúsculas>

[cuerpo opcional - qué y por qué, no el cómo]

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
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
1. git checkout development (crear si no existe: git checkout -b development)
2. [desarrollar, commits frecuentes en development]
3. Cuando Chris dice "pase a producción":
   a. git checkout main && git pull origin main
   b. git merge development
   c. Resolver conflictos si los hay
   d. Ejecutar /test-all
   e. git push origin main (= deploy automático)
4. Volver a development: git checkout development && git merge main
5. [si es release] git tag -a vX.X.X && git push origin vX.X.X
```

## Docker Deploy a Producción

El push a `main` activa GitHub Actions (`deploy-prod.yml`) que:
1. Ejecuta quality-gates (lint + test)
2. Security scan (Trivy)
3. Publica imágenes a GHCR (`ghcr.io/alpacapurpura/visionarias-{backend,frontend}:latest`)
