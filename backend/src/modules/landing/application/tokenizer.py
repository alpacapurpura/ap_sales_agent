"""Landing tokenizer — substitutes edition-level tokens in content trees.

Used by the edition clone flow (Phase 3) to turn a source edition's
landing into a target edition's landing by replacing date/location
tokens. Intentionally restrictive:

- Only the allowlist ``{{start_date}}``, ``{{end_date}}``, ``{{location}}``
  is recognised. Any other ``{{...}}`` token passes through unchanged so
  user-authored copy that happens to contain braces is never mangled.
- Only string leaves are touched; numeric / boolean / ``None`` values
  survive untouched. This keeps the function safe for arbitrary JSONB
  shapes that include prices, counts, feature flags, etc.
- The function is pure: inputs are not mutated; a fresh tree is returned.
  This lets callers compare "before" and "after" diffs without aliasing
  bugs, and makes the behaviour trivial to test.

The allowlist is a closed set; adding a new token is a deliberate code
change (and, typically, a matching UI affordance in the editor).
"""

from __future__ import annotations

import re

# Closed allowlist. Expanding the list requires updating copilot prompts,
# editor hints, and this regex in lockstep — worth the small maintenance
# cost because a runaway substitution corrupts user copy silently.
_ALLOWED_TOKENS: frozenset[str] = frozenset({"start_date", "end_date", "location"})
_TOKEN_RE = re.compile(r"\{\{(" + "|".join(_ALLOWED_TOKENS) + r")\}\}")

# The tokenizer walks arbitrary JSONB content trees (Puck block dicts,
# typed content VOs dumped to dict, raw user metadata). ``object`` is the
# right cue for "any JSON value" here; narrower typing (TypeAlias with
# Union) hurts readability without catching real bugs.
JSONNode = object  # pragma: no cover  — informational alias


def substitute_tokens(node: object, substitutions: dict[str, str]) -> object:
    """Return a deep-copied tree with edition tokens replaced.

    Only keys present in both the allowlist AND ``substitutions`` are
    substituted. Missing keys leave the token intact — call sites
    decide whether a missing substitution is an error (they can
    pre-validate) or acceptable (leave it for later rendering).
    """
    if isinstance(node, str):
        return _TOKEN_RE.sub(
            lambda m: substitutions.get(m.group(1), m.group(0)),
            node,
        )
    if isinstance(node, list):
        return [substitute_tokens(item, substitutions) for item in node]
    if isinstance(node, dict):
        return {key: substitute_tokens(value, substitutions) for key, value in node.items()}
    return node


__all__ = ["substitute_tokens"]
