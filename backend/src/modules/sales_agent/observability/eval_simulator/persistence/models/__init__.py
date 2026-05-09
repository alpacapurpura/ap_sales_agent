"""SQLAlchemy models for eval_simulator observability + grader tables.

Exposes:
- EvalSimulatorLlmCallModel      — eval_simulator_llm_call table mirror (Story B)
- EvalSimulatorTraceEventModel   — eval_simulator_trace_event table mirror (Story B)
- EvalSyntheticTenantModel       — eval_synthetic_tenants lookup table (Story B)
- EvalSimulatorGradeModel        — eval_simulator_grade table mirror (Story E T-2)
- EvalSimulatorGradeCacheModel   — eval_simulator_grade_cache table mirror (Story E T-2)

Origin:
- Story B: PI-12 eval-foundation-simulator-homologation (2026-05-07)
- Story E: PI-12 sales-agent-voice-fidelity-grader-runtime (2026-05-09, R5 schema-mirror exception)
"""

from __future__ import annotations

from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_grade import (
    EvalSimulatorGradeModel,
)
from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_grade_cache import (
    EvalSimulatorGradeCacheModel,
)
from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_llm_call import (
    EvalSimulatorLlmCallModel,
)
from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_trace_event import (
    EvalSimulatorTraceEventModel,
)
from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_synthetic_tenants import (
    EvalSyntheticTenantModel,
)

__all__ = [
    "EvalSimulatorGradeCacheModel",
    "EvalSimulatorGradeModel",
    "EvalSimulatorLlmCallModel",
    "EvalSimulatorTraceEventModel",
    "EvalSyntheticTenantModel",
]
