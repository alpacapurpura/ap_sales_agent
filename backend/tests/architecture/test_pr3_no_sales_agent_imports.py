"""Architecture guard — PR-3 LLM cost optimization MUST NOT touch sales_agent.

D-10 (CONTRACT PR-3): copilot/infrastructure/llm/* + copilot/evals/* MUST NOT
import from src.modules.sales_agent.* (rule sales-agent-brand-voice — voice
fidelity grader pendiente Q3 2026, sales_agent voice swap defer entirely).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR3_PATHS = [
    REPO_ROOT / "src" / "modules" / "copilot" / "infrastructure" / "llm",
    REPO_ROOT / "src" / "modules" / "copilot" / "evals",
]


def test_pr3_files_have_no_sales_agent_imports() -> None:
    """Scan all PR-3 source files for sales_agent imports."""
    violations: list[str] = []
    for base in PR3_PATHS:
        if not base.exists():
            continue
        for py_file in base.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "src.modules.sales_agent" in stripped or "from src.modules.sales_agent" in stripped:
                    rel = py_file.relative_to(REPO_ROOT)
                    violations.append(f"{rel}: {stripped}")

    assert not violations, (
        "PR-3 (LLM cost optimization) MUST NOT import from sales_agent (D-10 CONTRACT). "
        "Violations:\n  - " + "\n  - ".join(violations)
    )
