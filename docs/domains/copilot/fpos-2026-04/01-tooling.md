# Tooling F-pos

Hereda íntegro `docs/domains/copilot/testing-2026-04/01-tooling.md` (DeepEval + Chrome DevTools MCP + infra interna + CopilotJudge).

---

## Adiciones FP-specific

### FP1 (cross-stack mutations)

| Tool | Uso |
|---|---|
| **httpx async client** | Test BE endpoint apply via FastAPI TestClient o httpx.AsyncClient |
| **Vitest + Testing Library** | Test FE ProposalCard component re-render + fetch mock |
| **Playwright** (existing) | E2E re-run J1 click_apply post-fix |
| **Alembic raw SQL** | Migration idempotente para unique constraint en mutation_journal |

### FP2 (channel intent middleware)

| Tool | Uso |
|---|---|
| **pytest parametrize** | 20+ casos de phrasing por canal |
| **regex + unicodedata** | Accent + case insensitive detection |

### FP3 (routing parallel)

| Tool | Uso |
|---|---|
| **asyncio.gather + asyncio.wait** | Coalesce routing_decision con model warm-up |
| **time.monotonic_ns** | Measure TTFB con precision ms |
| **Chrome DevTools `performance_start_trace`** | Browser-side TTFB perception measurement |

### FP4 (voseo cleanup ratchet)

| Tool | Uso |
|---|---|
| **Path.rglob + re.compile** | Scanner unicode-aware ya implementado en B23-TP11 |
| **Arch fitness allowlist pattern** | Allow-shrink-only ratchet (heredado B23-TP11) |

---

## Anti-patterns tooling F-pos

- NO instalar deps nuevas si no es estrictamente necesario.
- NO refactor del stack tooling existente — F-pos cierra bugs, no migra herramientas.
- NO usar Chrome DevTools MCP en CI — solo verification manual.
