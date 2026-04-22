"""Token counting helper.

Uses ``tiktoken`` when available with CONTRACT-specified ``cl100k_base``
encoding. Falls back to a 4-chars-per-token heuristic if the lib is absent
(e.g. minimal environments).
"""

from __future__ import annotations

try:
    import tiktoken as _tiktoken

    _HAS_TIKTOKEN = True
except ImportError:  # pragma: no cover — env without tiktoken
    _tiktoken = None  # type: ignore[assignment]
    _HAS_TIKTOKEN = False


_ENCODING_CACHE: dict[str, object] = {}


def count_tokens(text: str, encoding: str = "cl100k_base") -> int:
    """Return the token count for ``text``.

    When ``tiktoken`` is available, uses ``encoding`` (default ``cl100k_base``).
    Otherwise returns ``len(text) // 4`` (OpenAI-style rough approximation).
    """
    if not text:
        return 0
    if not _HAS_TIKTOKEN or _tiktoken is None:
        return max(1, len(text) // 4)
    enc = _ENCODING_CACHE.get(encoding)
    if enc is None:
        enc = _tiktoken.get_encoding(encoding)
        _ENCODING_CACHE[encoding] = enc
    return len(enc.encode(text))  # type: ignore[attr-defined]
