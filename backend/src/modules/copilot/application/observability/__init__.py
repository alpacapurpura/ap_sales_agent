"""Legacy observability namespace — kept only for ``judge`` + ``rag_goldens``.

The Phase 2 atomic switch removed ``trace_recorder`` / ``node_trace`` /
``usage_tracking``. Two unrelated quality-evaluation utilities still live
here (``judge.py``, ``rag_goldens.py``) — they are imported by Phase 3
quality workers and have no relationship to the rebuild. Move them to a
quality-specific package the next time someone touches them.
"""
