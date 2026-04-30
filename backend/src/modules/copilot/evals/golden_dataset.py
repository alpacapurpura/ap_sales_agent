"""Golden dataset loader — D-4 (CONTRACT PR-3).

Loads JSONL golden files from ``evals/goldens/{use}/`` and validates
each line against the Pydantic schemas.

Classifier golden schema::

    {"id": "cls-001", "input_route": "/brand-studio",
     "input_user_msg": "Hola", "input_mode": "chat",
     "input_available_tool_count": 12,
     "expected_tier": "nano", "category": "greeting", "notes": "..."}

Summarizer golden schema::

    {"id": "sum-001", "previous_summary": "...",
     "displaced_messages": [{"role": "user", "content": "..."}],
     "max_chars": 400, "reference_summary": "...",
     "category": "casual_chat", "notes": "..."}
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

# Path to the goldens directory (relative to this file).
_GOLDENS_DIR = Path(__file__).parent / "goldens"


# ── Pydantic schemas ─────────────────────────────────────────────────────────


class ClassifierGolden(BaseModel):
    """One classifier golden example."""

    model_config = ConfigDict(extra="ignore")

    id: str
    input_route: str
    input_user_msg: str
    input_mode: str = "chat"
    input_available_tool_count: int = 0
    expected_tier: str  # "nano" | "mini" | "reasoning" | "heavy"
    category: str
    notes: str = ""


class SummarizerMessage(BaseModel):
    """A single message in a summarizer golden displaced_messages list."""

    model_config = ConfigDict(extra="ignore")

    role: str
    content: str


class SummarizerGolden(BaseModel):
    """One summarizer golden example."""

    model_config = ConfigDict(extra="ignore")

    id: str
    previous_summary: str = ""
    displaced_messages: list[SummarizerMessage] = Field(default_factory=list)
    max_chars: int = 400
    reference_summary: str
    category: str
    notes: str = ""


# ── Loaders ──────────────────────────────────────────────────────────────────


def _load_jsonl(path: Path) -> list[dict]:  # type: ignore[type-arg]
    """Load all valid JSON lines from ``path``; skip blank lines."""
    records: list[dict] = []  # type: ignore[type-arg]
    with path.open(encoding="utf-8") as fh:
        for line_num, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                msg = f"Invalid JSON at {path}:{line_num} — {exc}"
                raise ValueError(msg) from exc
    return records


def load_classifier_goldens(filename: str = "nano_routing.jsonl") -> list[ClassifierGolden]:
    """Load classifier goldens from ``goldens/classifier/<filename>``."""
    path = _GOLDENS_DIR / "classifier" / filename
    if not path.exists():
        msg = f"Golden file not found: {path}"
        raise FileNotFoundError(msg)
    records = _load_jsonl(path)
    return [ClassifierGolden.model_validate(r) for r in records]


def load_summarizer_goldens(
    filename: str = "conversation_compress.jsonl",
) -> list[SummarizerGolden]:
    """Load summarizer goldens from ``goldens/summarizer/<filename>``."""
    path = _GOLDENS_DIR / "summarizer" / filename
    if not path.exists():
        msg = f"Golden file not found: {path}"
        raise FileNotFoundError(msg)
    records = _load_jsonl(path)
    return [SummarizerGolden.model_validate(r) for r in records]


def load_all_classifier_goldens() -> list[ClassifierGolden]:
    """Load all classifier golden files (main + adversarial)."""
    all_goldens: list[ClassifierGolden] = []
    for jsonl_file in sorted((_GOLDENS_DIR / "classifier").glob("*.jsonl")):
        all_goldens.extend(load_classifier_goldens(jsonl_file.name))
    return all_goldens


def load_all_summarizer_goldens() -> list[SummarizerGolden]:
    """Load all summarizer golden files (main + adversarial)."""
    all_goldens: list[SummarizerGolden] = []
    for jsonl_file in sorted((_GOLDENS_DIR / "summarizer").glob("*.jsonl")):
        all_goldens.extend(load_summarizer_goldens(jsonl_file.name))
    return all_goldens
