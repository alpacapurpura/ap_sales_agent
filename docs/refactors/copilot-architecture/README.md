# Refactor: Copilot Extractor + Focus Mode

Workspace para refactor arquitectónico. Año 2026, abril. Branch base: `development`.

## Estado

**Fase actual**: research. Sin código aún. Gate: responder `OPEN-QUESTIONS.md`.

## Documentos

| Archivo | Propósito |
|---|---|
| [INVESTIGATION.md](INVESTIGATION.md) | Informe research: estado actual, gaps, patrones 2026, tradeoffs. |
| [PLAN.md](PLAN.md) | Plan por fases F0-F7. Dependencias, arch tests, exit criteria. |
| [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) | 6 decisiones humanas pendientes antes de código. |
| DECISIONS.md (por crear F0) | ADRs numerados. |
| STATE.md (por crear F0) | Hash tracking por fase. |
| INVARIANTS.md (por crear F0) | Qué nunca se rompe. |
| TODO.md (por crear F0) | Tareas operativas. |

## Misión

1. Contrato único tool response tipado (elimina JSON-regurgitation raíz).
2. Unificar flujos extracción URL+DOC (worker pattern, `commit_mode` flag).
3. Focus mode E2E (checkpointer + FocusState + FE sidebar dedicada + nav lock).
4. Registry dominios extensible (1 PR = nuevo dominio).
5. Persister Protocol común.
6. Observabilidad estructurada (session_id focus, OTel GenAI).
7. Retiro `output_sanitizer` cuando contrato enforced.
8. Context budget strategy para interviews largas.

## Paralelo-safe

- No toca módulos en curso refactor `field-contract-ssot` hasta F1.
- F0 = docs/ADRs, completamente seguro paralelo.

## Próximo paso

Responder OPEN-QUESTIONS → arranca F0.
