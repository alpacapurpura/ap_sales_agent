"""Pure functions to diff two aggregate model dumps by section.

Used by extraction workers (brand/offer) to compute what a worker run wrote,
so the copilot can surface a meaningful summary card + section pills even when
the extraction service itself doesn't emit per-wave progress.

Design constraints:
- Zero dependency on any domain/infrastructure layer. Takes ``dict`` in,
  returns primitives. Importable from anywhere — `shared → *` is safe.
- Section slug = the top-level key in the dump. Per-section field paths are
  dot-concatenated leaf paths.
- "Filled" ≡ non-None, non-empty string, non-empty list, non-empty dict,
  or any primitive (int/float/bool). Matches the intuition used by form-runtime.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "diff_filled_by_section",
    "filled_fields_by_section",
]


def _is_filled(value: Any) -> bool:  # noqa: ANN401 — recursive walker over JSON-like trees
    """Return True if ``value`` represents a populated field."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return len(value) > 0
    # int, float, bool, Decimal, etc. — presence is enough
    return True


def _walk_leaves(data: Any, prefix: str) -> list[str]:  # noqa: ANN401 — JSON walker
    """Return dotted paths of filled leaves under ``data``.

    - For primitives/strings: one path if filled, else none.
    - For dict: recurse into each key.
    - For list: treated as a single leaf (we don't enumerate indexes — the
      section-granularity summary doesn't need to distinguish list items).
    """
    if isinstance(data, dict):
        paths: list[str] = []
        for key, value in data.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(_walk_leaves(value, child_prefix))
        return paths

    # Leaf — include if filled and there's a path to report
    if prefix and _is_filled(data):
        return [prefix]
    return []


def filled_fields_by_section(dump: dict[str, Any]) -> dict[str, list[str]]:
    """Group filled leaf paths by top-level section key.

    Example:
        dump = {
          "identity": {"brand_name": "Visionarias", "tagline": ""},
          "strategy": {"mission": {"statement": "…"}},
          "visuals":  {},
        }
        → {
            "identity": ["identity.brand_name"],
            "strategy": ["strategy.mission.statement"],
            # "visuals" absent — nothing filled
          }

    Top-level keys that carry non-dict values (e.g. list aggregates like
    ``testimonials``) are reported as ``{key: [key]}`` when non-empty.
    """
    result: dict[str, list[str]] = {}
    for section_slug, section_payload in dump.items():
        if isinstance(section_payload, dict):
            leaves = _walk_leaves(section_payload, section_slug)
            if leaves:
                result[section_slug] = leaves
        elif _is_filled(section_payload):
            # non-dict top-level (e.g. a list aggregate) — treat the whole
            # section as a single filled path.
            result[section_slug] = [section_slug]
    return result


def diff_filled_by_section(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, list[str]]:
    """Return paths that became filled between ``before`` and ``after``.

    Only sections whose after-list grew (relative to before) are included.
    Empty sections are omitted, so callers can iterate the result to know
    which sections to announce to the UI.
    """
    before_map = filled_fields_by_section(before)
    after_map = filled_fields_by_section(after)

    delta: dict[str, list[str]] = {}
    for slug, paths in after_map.items():
        before_set = set(before_map.get(slug, []))
        new_paths = [p for p in paths if p not in before_set]
        if new_paths:
            delta[slug] = new_paths
    return delta
