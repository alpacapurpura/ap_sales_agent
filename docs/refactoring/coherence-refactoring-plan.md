# Plan de Refactoring: Coherencia Total del Codebase

**Objetivo:** Que todo el código parezca escrito por una sola persona. Auditorías + onboarding de devs.
**Fecha:** 2026-04-15
**Estado:** Pendiente de aprobación

---

## Diagnóstico Actual

| Métrica | Backend | Frontend |
|---------|---------|----------|
| Lint (0 errors) | PASS | PASS |
| Arch fitness tests | 10 gates, 68 tests | boundaries/dependencies enforced |
| Duplicación | 3.63% | 4.52% |
| Tests | 2803 (60.85% cov) | 1063 (25% cov) |
| Inconsistencias detectadas | 8 categorías | 12 categorías |

---

## FASE 1: Nuevos Arch Fitness Tests (Backend)

Protegen contra regresión. Se escriben ANTES de refactorear.

### 1.1 `test_no_httpexception_outside_api.py`

**Regla:** `HTTPException` solo en `api/` layer.
**Implementación:** Escanear imports de `fastapi.exceptions` o `starlette.exceptions` en `domain/`, `infrastructure/`, `application/`.
**Violaciones actuales:** 0 (PASS, pero sin test que lo proteja).

### 1.2 `test_consistent_logging.py`

**Regla:** Solo `structlog`. Prohibido `import logging` y `print()` en `src/`.
**Violaciones actuales:** ~20 archivos con `import logging`.
**Allowlist inicial:** los 20 archivos actuales. Ratchet hacia 0.

### 1.3 `test_pydantic_v2_only.py`

**Regla:** No `class Config:` (v1). Solo `model_config = ConfigDict(...)`.
**Violaciones actuales:** 6 archivos.
**Allowlist inicial:** los 6. Fix inmediato (mecánico).

### 1.4 `test_sqlalchemy_column_style.py`

**Regla:** Solo `mapped_column()` (SA 2.0). Prohibido `Column()` en modelos nuevos.
**Violaciones actuales:** ~35 archivos con `Column()`.
**Allowlist inicial:** los 35. Migrar progresivamente.

### 1.5 `test_repository_signatures.py`

**Regla:** Todo método público de repositorio recibe `tenant_id: UUID` como parámetro (excepto `shared/`).
**Violaciones actuales:** por cuantificar con test.
**Allowlist inicial:** dinámico.

### 1.6 `test_router_has_tags.py`

**Regla:** Todo `APIRouter()` debe tener `tags=[...]`.
**Violaciones actuales:** ~15 routers sin tags.

### 1.7 `test_no_optional_syntax.py`

**Regla:** Usar `X | None`, prohibido `Optional[X]`.
**Violaciones actuales:** ~4 archivos.
**Fix:** mecánico con ruff `UP007`.

### 1.8 `test_service_async_only.py`

**Regla:** Todo método público de service en `application/` debe ser `async def`.
**Excepciones:** Métodos de cómputo puro (no IO).
**Violaciones actuales:** por cuantificar.

---

## FASE 2: Nuevos Arch Fitness Tests (Frontend)

### 2.1 ESLint rule: `no-default-export` (custom)

**Regla:** `export default` solo en `app/**/page.tsx`, `app/**/layout.tsx`, `app/**/loading.tsx`.
**Violaciones actuales:** 42 archivos.
**Implementación:** `eslint-plugin-import` rule `no-default-export` con override para `app/`.

### 2.2 ESLint rule: `no-inline-styles`

**Regla:** Prohibido `style={{}}` en JSX. Solo Tailwind.
**Violaciones actuales:** 162 atributos.
**Implementación:** `react/forbid-component-props` con pattern en `style`.
**Modo:** warn inicialmente, error cuando se limpie.

### 2.3 ESLint rule: `no-direct-fetch`

**Regla:** Prohibido `fetch()` y `axios()` en `features/`. Solo `fetchClient` desde `api/` folders.
**Violaciones actuales:** 14 calls directos.
**Implementación:** `no-restricted-globals` para `fetch` en features, con override en `api/` subdirs.

### 2.4 Vitest: `test_feature_has_api_folder.test.ts`

**Regla:** Toda feature con data fetching tiene carpeta `api/` con funciones tipadas.
**Violaciones actuales:** 6 de 13 features sin `api/`.
**Implementación:** test que lista features y verifica estructura.

### 2.5 Vitest: `test_no_type_assertions.test.ts`

**Regla:** Cero `as any`, `@ts-ignore`, `@ts-expect-error`.
**Violaciones actuales:** 34 `as any`, 8 `@ts-ignore`.
**Implementación:** grep-based test con allowlist ratchet.

---

## FASE 3: Fixes Mecánicos (Bajo Riesgo, Alto Impacto)

Cambios que se pueden hacer masivamente sin riesgo funcional.

### Backend

| # | Fix | Archivos | Esfuerzo | Riesgo |
|---|-----|----------|----------|--------|
| 3.1 | `class Config:` → `model_config = ConfigDict(...)` | 6 | 15 min | Nulo |
| 3.2 | `Optional[X]` → `X \| None` | 4 | 5 min | Nulo |
| 3.3 | `import logging` → `import structlog` (adaptar calls) | 20 | 2 hrs | Bajo |
| 3.4 | `asyncio.get_event_loop().run_until_complete()` → `async/await` en tests | 2 done, verificar más | 30 min | Nulo |
| 3.5 | Agregar `tags=` a routers sin tags | 15 | 30 min | Nulo |
| 3.6 | `Column()` → `mapped_column()` en modelos | 35 | 3 hrs | Bajo |
| 3.7 | Normalizar nombres de métodos de repo: `get_by_id`, `get_all`, `create`, `update`, `delete` | 20+ | 4 hrs | Medio |

### Frontend

| # | Fix | Archivos | Esfuerzo | Riesgo |
|---|-----|----------|----------|--------|
| 3.8 | `export default` → named export (non-pages) | 42 | 2 hrs | Bajo |
| 3.9 | `as any` → tipos correctos o `unknown` | 34 | 3 hrs | Bajo |
| 3.10 | `@ts-ignore` → fix real o `@ts-expect-error` con comment | 8 | 1 hr | Bajo |
| 3.11 | `style={{}}` → clases Tailwind | 162 | 8 hrs | Medio |
| 3.12 | Crear `api/` folder en 6 features sin ella | 6 features | 4 hrs | Medio |
| 3.13 | Archivos >350 líneas → split en componentes | 20 files | 8 hrs | Medio |

---

## FASE 4: Patrones Canónicos (Documentar + Enforcer)

Para cada patrón, crear:
1. **Ejemplo canónico** en `docs/patterns/`
2. **Arch fitness test** que lo enforce
3. **Template** para scaffolding

### 4.1 Backend: Módulo Canónico

```
modules/{name}/
  __init__.py
  domain/
    __init__.py
    {name}.py              # Entidad/aggregate root
    value_objects.py        # Value objects (si aplica)
    events.py              # Domain events (si aplica)
    exceptions.py           # Domain exceptions
    ports.py               # Repository interfaces
  infrastructure/
    __init__.py
    {name}_repository.py    # SQLAlchemy repo (implements ports)
    {name}_model.py         # SQLAlchemy model (mapped_column only)
  application/
    __init__.py
    {name}_service.py       # Async service, orchestrates domain + infra
    dto/
      __init__.py
      {name}_dto.py         # Pydantic v2, model_config = ConfigDict(...)
  api/
    __init__.py
    {name}_router.py        # APIRouter(prefix=..., tags=[...])
    dependencies.py         # Depends() factories
```

**Convenciones del módulo canónico:**

| Aspecto | Estándar |
|---------|----------|
| Models | `mapped_column()`, `DateTime(timezone=True)`, `deleted_at` soft delete |
| Repos | `async` methods, `tenant_id: UUID` primer param, returns domain entities |
| Naming | `get_by_id`, `get_all`, `create`, `update`, `soft_delete` |
| Services | `async def`, reciben `tenant_id`, lanzan domain exceptions |
| DTOs | `model_config = ConfigDict(from_attributes=True)`, `X \| None` |
| Routers | `response_model=`, `tags=`, thin (max 10 lines por endpoint) |
| Logging | `structlog.get_logger()` at module level |
| Errors | Domain exceptions in `domain/exceptions.py`, mapped to HTTP in `api/` |

### 4.2 Frontend: Feature Canónica

```
features/{name}/
  index.ts                  # Barrel: re-exports públicos
  api/
    {name}-api.ts            # fetchClient calls, typed responses
  components/
    {Name}Page.tsx           # PascalCase, named export
    {Name}Form.tsx           # RHF + Zod
    {Name}List.tsx
  hooks/
    use-{name}.ts            # Custom hooks wrapping useQuery/useMutation
  types/
    {name}.types.ts          # Interfaces/types
  utils/
    {name}.utils.ts          # Pure functions
  config/
    {name}.config.ts         # Constants, display maps
```

**Convenciones de la feature canónica:**

| Aspecto | Estándar |
|---------|----------|
| Components | PascalCase file, named export, `"use client"` solo si interactivo |
| Props | `interface {Name}Props { ... }` (no `type`, no inline) |
| Data fetch | `useQuery`/`useMutation` en `hooks/`, nunca en componente directo |
| API calls | Solo en `api/` folder, usando `fetchClient` |
| Forms | React Hook Form + Zod schema, nunca `useState` manual |
| Styling | Tailwind + `cn()`, cero `style={{}}`, cero hex hardcoded |
| Exports | Named exports always. `export default` solo en `page.tsx` |
| Types | `unknown` + type guards, cero `as any`, cero `@ts-ignore` |
| Error states | Todo `useQuery` maneja `isLoading`, `isError`, `error` |
| Loading | Skeleton components, nunca `"Loading..."` strings |

---

## FASE 5: Archivos Grandes → Split

Los 10 peores ofensores. Cada uno necesita refactor dedicado.

| Archivo | Líneas | Acción |
|---------|--------|--------|
| `SidebarContent.tsx` | 1087 | Split: NavSection, NavItem, SidebarHeader, SidebarFooter |
| `meta-view.tsx` | 1085 | Split: MetaOverview, MetaAdsTab, MetaPixelTab |
| `metrics-mock.ts` | 1029 | Split por stage: attraction-mock, capture-mock, etc. |
| `CampaignsTab.tsx` | 991 | Split: CampaignList, CampaignCard, CampaignFilters |
| `connections.ts` | 929 | Split por provider: meta-api, google-api, shopify-api |
| `brand-visuals-wizard.tsx` | 800+ | Split: steps como componentes separados |
| `ChannelDetailSidebar.tsx` | 700+ | Split: SidebarHeader, SidebarMetrics, SidebarChart |
| `google-analytics-view.tsx` | 600+ | Split: GAOverview, GAMetrics, GAConfig |
| `youtube-view.tsx` | 600+ | Split: YTOverview, YTMetrics |
| `google-workspace-view.tsx` | 600+ | Split: mismo patrón |

---

## FASE 6: Verificación Continua

### CI Pipeline (agregar a `.github/workflows/deploy-prod.yml`)

```yaml
- name: Arch Fitness Tests
  run: cd backend && .venv/bin/pytest tests/architecture/ -x -q

- name: Frontend Structure Tests
  run: cd frontend && npx vitest run src/__tests__/architecture/
```

### Pre-commit (opcional, para devs nuevos)

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: arch-fitness
      name: Architecture fitness
      entry: bash -c 'cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=line'
      language: system
      pass_filenames: false
```

### Checklist para nuevos módulos/features

- [ ] Sigue estructura canónica (4.1 backend / 4.2 frontend)
- [ ] Arch fitness tests pasan
- [ ] 0 lint errors
- [ ] Tests escritos (TDD)
- [ ] No `as any`, no `@ts-ignore`, no `export default`
- [ ] No `style={{}}`, no `import logging`, no `class Config:`
- [ ] Archivos < 350 líneas
- [ ] `tenant_id` en todo repo method

---

## Orden de Ejecución Recomendado

| Prioridad | Fase | Descripción | Esfuerzo | Impacto |
|-----------|------|-------------|----------|---------|
| **P0** | 1 (parcial) | Tests 1.1-1.4 (protección inmediata) | 2 hrs | Bloquea nuevas inconsistencias |
| **P0** | 3.1-3.5 | Fixes mecánicos backend (0 riesgo) | 3 hrs | Limpieza visible inmediata |
| **P1** | 1 (resto) | Tests 1.5-1.8 | 3 hrs | Cobertura completa backend |
| **P1** | 3.8-3.10 | Fixes mecánicos frontend (bajo riesgo) | 4 hrs | Limpieza visible frontend |
| **P2** | 2 | ESLint rules frontend | 2 hrs | Protección frontend |
| **P2** | 4 | Documentar patrones canónicos | 3 hrs | Onboarding de devs |
| **P3** | 3.6-3.7, 3.11-3.13 | Fixes de medio riesgo | 20 hrs | Consistencia profunda |
| **P3** | 5 | Split archivos grandes | 16 hrs | Mantenibilidad |
| **P4** | 6 | CI + pre-commit | 2 hrs | Automatización |

**Total estimado: ~55 horas de trabajo.**
**Resultado: codebase que pasa auditoría y onboarding sin fricción.**

---

## Métricas de Éxito

| Métrica | Hoy | Meta |
|---------|-----|------|
| Arch fitness tests | 10 | 18+ |
| Backend `import logging` | 20 | 0 |
| Backend `class Config:` | 6 | 0 |
| Backend `Column()` | 35 | 0 |
| Frontend `export default` (non-page) | 42 | 0 |
| Frontend `as any` | 34 | 0 |
| Frontend `style={{}}` | 162 | 0 |
| Frontend features sin `api/` | 6 | 0 |
| Archivos >350 líneas | 20 | 0 |
| ESLint warnings | 5863 | <3000 |
