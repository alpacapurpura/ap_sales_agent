"""Anti-creep guard: no separate brand_voice_summary table or LLM-distilled
summary may exist alongside the SSoT ``personality_profiles.system_instruction``.

The 2026-04-28 architecture decision (`.claude/rules/sales-agent-brand-voice.md`)
fixed PersonalityProfile + 6-block compiler as the single source of truth for
brand voice. A summary mirror table would (a) duplicate state, (b) drift from
the compiled instruction, (c) introduce LLM nondeterminism in a path that is
currently fully deterministic.

This test fails CI when:
- Any class is named ``BrandVoiceSummary*``, ``VoiceSummary*``, or similar.
- A SQLA model declares a tablename matching ``brand_voice_summary*``.
- An ARQ task is registered with name ``regenerate_brand_voice_summary``.
- A function is named ``polish_brand_voice`` / ``rewrite_brand_voice`` (would
  imply a post-generation rewriter LLM pass — explicitly forbidden).
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

FORBIDDEN_PATTERNS: tuple[tuple[str, str], ...] = (
    # (regex pattern, human-readable reason)
    (
        r"class\s+BrandVoiceSummary\w*\b",
        "BrandVoiceSummary* class — duplicates personality_profiles SSoT.",
    ),
    (
        r"class\s+VoiceSummary\w*\b",
        "VoiceSummary* class — duplicates personality_profiles SSoT.",
    ),
    (
        r"__tablename__\s*=\s*['\"]brand_voice_summary",
        "brand_voice_summary table — duplicates personality_profiles SSoT.",
    ),
    (
        r"def\s+regenerate_brand_voice_summary\b",
        "regenerate_brand_voice_summary worker — forbidden by SSoT rule.",
    ),
    (
        r"def\s+polish_brand_voice\b",
        "polish_brand_voice — voice-rewriter LLM pass is forbidden (2x cost, 0 gain).",
    ),
    (
        r"def\s+rewrite_brand_voice\b",
        "rewrite_brand_voice — voice-rewriter LLM pass is forbidden.",
    ),
)


def test_no_brand_voice_summary_creep() -> None:
    """Scan the source tree for any forbidden brand-voice-summary patterns."""
    offenders: list[tuple[Path, int, str, str]] = []

    for py_file in SRC_ROOT.rglob("*.py"):
        # Skip the rule reminder file itself if it ever ends up under src/
        relative = py_file.relative_to(PROJECT_ROOT)
        try:
            text = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for pattern, reason in FORBIDDEN_PATTERNS:
            for match in re.finditer(pattern, text):
                # Compute line number for the offender
                line_no = text[: match.start()].count("\n") + 1
                offenders.append((relative, line_no, match.group(0), reason))

    if offenders:
        msg_lines = [
            "Brand voice SSoT creep detected. See .claude/rules/sales-agent-brand-voice.md.",
            "",
        ]
        for path, line_no, snippet, reason in offenders:
            msg_lines.append(f"  {path}:{line_no} → {snippet!r} :: {reason}")
        raise AssertionError("\n".join(msg_lines))
