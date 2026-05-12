# T-16 impl-log

**Ticket:** T-16 (Story 7 luana-sales-agent-engine)
**Owner:** builder-agentic Opus 4.7 (R23)
**Started:** 2026-05-12
**Completed:** 2026-05-12
**Commit:** `6625646` (luana-platform)

## Scope

Replace `NotImplementedError` stub in luana-core-connections api/
dependencies composition root with real `ChatOrchestrator` wiring.
Resolves Stories 4+6 deferral now that both luana_core_copilot AND
luana_core_sales_agent exist in luana-platform.

## Skills Consulted

- **copilot-expert** (auto-loaded slot): cross-module DI composition
  root patterns — confirmed connections api/dependencies is the
  canonical DDD exception (composition root owns cross-module imports).
- **sales-agent-expert** (auto-loaded slot): §3 protected surface list
  confirms `chat.py::ChatOrchestrator` is NOT in §3 list (orchestrator
  pattern itself is non-protected) — wiring it as MessageHandlerPort
  implementation is allowed.
- **tessl__langgraph**: not invoked — pure DI wiring, no graph changes.
- **tessl__graceful-degradation**: not invoked — no new external calls.

## Implementation

### Step 1 — Read AISALESHT source code

```python
# backend/src/modules/connections/api/dependencies/__init__.py (verbatim)
from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator
from src.shared.links.ports.message_handler import MessageHandlerPort

_message_handler: MessageHandlerPort = ChatOrchestrator()


def get_message_handler() -> MessageHandlerPort:
    return _message_handler
```

### Step 2 — sed import paths

Mechanical rewrite per 05-guidelines.md §1.4:

- `src.modules.sales_agent.` → `luana_core_sales_agent.`
- `src.shared.links.ports.message_handler` → `luana_core_platform.links.ports.message_handler`

### Step 3 — File rewrite

`core/luana-core-connections/src/luana_core_connections/api/dependencies/
__init__.py`: stub `raise NotImplementedError` REPLACED with real
ChatOrchestrator singleton wiring.

### Step 4 — Connections tests revealed cascade

Initial `uv run pytest core/luana-core-connections/tests/` after wiring
failed with `MessageModel` table collision: the conftest declared a
STUB `MessageModel` on `Base.metadata` (Story 4 stub pending Story 7
lift). With T-16 wiring, the real `MessageModel` (from
`luana_core_sales_agent.infrastructure.models.message_model`) gets
transitively imported via `ChatOrchestrator` — collision with the
stub.

Fix: register the real `MessageModel` FIRST in conftest, so the stub
guard `if "messages" not in Base.metadata.tables:` skips:

```python
# Story 7 T-16: Register real sales_agent.MessageModel BEFORE stub guard runs.
from luana_core_sales_agent.infrastructure.models.message_model import MessageModel  # noqa: F401
```

### Step 5 — LeadModel relationship cascade

Second cascade: `LeadModel.messages = relationship("MessageModel",
foreign_keys="MessageModel.lead_id", ...)`. The real `MessageModel`
has column `user_id` (with `lead_id` as a Python `@property` — backward
compat); `lead_id` is NOT a mapped column. Story 4 wrote `foreign_keys=
"MessageModel.lead_id"` assuming the lift would create that column.

Fix per AISALESHT SSoT (`backend/src/shared/infrastructure/models/crm.
py:201`):

```python
messages = relationship(
    "MessageModel",
    back_populates="lead",      # matches MessageModel.lead relationship
    cascade="all, delete-orphan",
)
```

The real MessageModel has `lead = relationship("LeadModel",
back_populates="messages", foreign_keys=[user_id])` — pairs cleanly with
`back_populates="lead"` on LeadModel side.

`AppointmentModel` relationship retains `foreign_keys=
"AppointmentModel.lead_id"` (still stub-targeted — Story 8 lift
pending).

## Results

```bash
cd ~/luana-platform && uv run pytest core/luana-core-connections/tests/ -x -q --tb=short
# Result: 218/218 PASS (100%)
# Pre-T-16 baseline: 53 tests PASS (stub state)
```

Smoke test:

```bash
$ uv run python -c "
from luana_core_connections.api.dependencies import get_message_handler
handler = get_message_handler()
print(handler.__class__.__name__)"
# Output: ChatOrchestrator
```

## Validators GREEN

- **V-F-py-3** GREEN: `core/luana-core-connections/tests/` 218/218 PASS
  with real ChatOrchestrator wiring.

## Files Changed (luana-platform)

```
M core/luana-core-connections/src/luana_core_connections/api/dependencies/__init__.py
M core/luana-core-connections/tests/conftest.py
M core/luana-core-platform/src/luana_core_platform/infrastructure/models/crm.py
```

3 files changed, 39 insertions(+), 35 deletions(-).

## AISALESHT Impact

**ZERO** — V-NF-4 invariant preserved. AISALESHT not touched.

## Halt Criteria Status

- [x] AISALESHT UNTOUCHED — verified
- [x] D-T3 cardinal preserved — no PersonalityCompiler imports touched
- [x] D-T6 anti-mirror preserved — no observability changes
- [x] §3 hash-stable preserved — no §3 files modified
- [x] ChatOrchestrator wiring works — smoke test confirms

## Deferral Resolution

Stories 4+6 deferral CLOSED via T-16. `luana_core_connections.api.
dependencies.get_message_handler` now returns real `ChatOrchestrator`
instance (not `NotImplementedError`).
