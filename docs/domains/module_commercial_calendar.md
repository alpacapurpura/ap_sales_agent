---
module: Commercial Calendar
status: active
---

# Commercial Calendar

Calendario de eventos comerciales (feriados, campanas, cyber days, temporadas) filtrado por pais. Alimenta al Growth Studio y al Sales Agent con contexto temporal para acciones de marketing oportunas.

## Conceptos de Dominio

- **Eventos de sistema** (`tenant_id=NULL`): feriados nacionales, campanas universales. No pueden ser eliminados por tenants.
- **Eventos de tenant** (`tenant_id=UUID`): eventos custom creados por el usuario (lanzamientos, promos propias).
- **Decomposicion multi-dia**: al crear un evento con `date_start` y `date_end`, el servicio genera una fila por dia, cada una con su `week_number` e `year` calculados via ISO calendar.
- **EventCategory**: `feriado`, `campana`, `cyber`, `sale`, `dia_especial`, `temporada`, `cultural`, `elecciones`, `custom`.

## Decisiones de Arquitectura

- `country_code` (ISO 3166-1 alpha-2) como filtro obligatorio en todas las queries. Permite escalar a multiples mercados sin duplicar logica.
- Las queries de listado devuelven `sistema + tenant` combinados: `WHERE tenant_id IS NULL OR tenant_id = :tid`.
- `week_number` pre-calculado en cada fila para filtrado rapido por semana (endpoint `current-week`).

## Reglas de Negocio

- Solo el tenant dueno puede editar/eliminar sus eventos. Eventos de sistema son read-only para tenants.
- Soft delete via `deleted_at` en todas las operaciones de borrado.

## CRITICO — No Violar

- Nunca permitir que un tenant modifique o elimine un evento con `tenant_id=NULL`.
- Siempre filtrar por `country_code` — no existe endpoint de "todos los paises".
