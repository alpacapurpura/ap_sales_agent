"""Sales-agent tool registry hierarchy.

Per-domain sub-packages live here:

* ``scheduling/`` — booking-link / availability / verify (S8).
* ``payment/``    — payment-link / verify / grant-access (S9, planned).

Each sub-package owns its provider strategy + tool functions; the
top-level ``TOOL_REGISTRY`` (still in ``application/agents/sales/tools.py``
for backward compatibility) merges them via dict-spread.
"""
