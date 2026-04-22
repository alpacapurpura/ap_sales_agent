"""Prompt injection sanitization for Copilot system prompts.

User-provided field values (brand name, description, interview answers, etc.)
are inserted into Jinja2 system prompts. Without sanitization, a malicious
value like "Ignore all previous instructions..." could manipulate the LLM.

Defence strategy:
  1. Wrap every user-controlled string in <user_data>…</user_data> XML tags.
     The system prompt instructs the model to treat content inside those tags
     as data, NOT as instructions.
  2. Truncate values that exceed MAX_USER_VALUE_LENGTH to prevent context flooding.
  3. Escape any occurrence of the closing tag inside the value itself, so a
     crafted payload cannot break out of the wrapper.

Usage (in graph.py before prompt_loader.render()):
    from src.modules.copilot.infrastructure.prompts.sanitizer import (
        sanitize_selected_fields,
        sanitize_mapa_global,
    )
"""

from __future__ import annotations

from typing import Any

# Maximum number of characters allowed for any single user-provided value.
# Values longer than this are truncated before wrapping.
MAX_USER_VALUE_LENGTH = 2000

_OPEN_TAG = "<user_data>"
_CLOSE_TAG = "</user_data>"
# Escape the closing tag that appears inside the user value so it cannot
# prematurely terminate the wrapper.
_ESCAPED_CLOSE = "&lt;/user_data&gt;"


def sanitize_user_value(value: Any) -> str:  # noqa: ANN401 — intentional Any for coercion
    """Wrap a single user-provided value in XML delimiters.

    - Returns ``""`` for None and empty strings (no tag needed).
    - Coerces non-string primitives to ``str`` before wrapping.
    - Truncates strings that exceed MAX_USER_VALUE_LENGTH.
    - Escapes any ``</user_data>`` that appears inside the value.
    """
    if value is None:
        return ""

    text = str(value)

    if not text:
        return ""

    # Escape any closing tag in the value to prevent breakout
    text = text.replace(_CLOSE_TAG, _ESCAPED_CLOSE)

    # Truncate if necessary
    if len(text) > MAX_USER_VALUE_LENGTH:
        text = text[:MAX_USER_VALUE_LENGTH] + " [truncated]"

    return f"{_OPEN_TAG}{text}{_CLOSE_TAG}"


def sanitize_selected_fields(
    fields: list[Any],
) -> list[Any]:
    """Return a sanitized copy of the selected_fields list.

    Each dict entry's ``field_label`` and ``field_value`` are wrapped.
    Non-dict entries and other keys are left unchanged.
    """
    result = []
    for entry in fields:
        if not isinstance(entry, dict):
            result.append(entry)
            continue
        sanitized = dict(entry)
        if "field_value" in sanitized:
            sanitized["field_value"] = sanitize_user_value(sanitized["field_value"])
        if "field_label" in sanitized:
            sanitized["field_label"] = sanitize_user_value(sanitized["field_label"])
        result.append(sanitized)
    return result


def sanitize_mapa_global(
    mapa: dict[str, Any],
) -> dict[str, Any]:
    """Return a sanitized copy of the interview mapa_global dict.

    Interview values are typically strings (user answers). Lists/dicts
    (e.g. structured sub-fields) are left unchanged.
    None values are converted to ``""`` (no tag).
    """
    result: dict[str, Any] = {}
    for key, value in mapa.items():
        if value is None:
            result[key] = ""
        elif isinstance(value, str):
            result[key] = sanitize_user_value(value)
        else:
            result[key] = value
    return result
