# Phase 3 — Deferred Debt (TEMPLATE — llenar al cerrar fase)

> Items que se descubrieron y NO entraron al alcance de Fase 3.
> Como esta es la última fase del rebuild, items relevantes van a `docs/mejoras-proceso/to-do.md` (regla 12 de CLAUDE.md), no a una "Fase 4".

---

## Items de Fase 3 NO completados

- (vacío si todos completados)

---

## Items movidos a `docs/mejoras-proceso/to-do.md`

> Format: descripción + razón por la que no entró al rebuild.

- (ej. "PII redaction async con Presidio — overhead síncrono no aceptable; queda regex sincrónico + queda pendiente worker async")
- (ej. "Email/Slack para cost alerts — no hay infra de email aún en el proyecto")

---

## Mejoras post-rebuild sugeridas (opcionales, no urgentes)

- ...

---

## Notas para futuras evoluciones

- ¿Cuándo migrar a TimescaleDB? Trigger: cuando volumen `copilot_llm_call` supere X rows/mes.
- ¿Cuándo adoptar Langfuse/LangSmith hosted? Trigger: cuando equipo crezca y necesite UI compartida de eval.
- ¿Cuándo exportar a OTel collector? Trigger: cuando otro módulo del repo adopte OTel y haya valor en consolidar.
