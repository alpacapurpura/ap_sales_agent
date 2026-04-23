"""Copilot observability — per-turn trace recorder.

Writes structured events into ``copilot_trace_event`` so every /copilot/chat
request leaves a replayable breadcrumb trail: LLM calls with token counts,
tool invocations with args/output, card emissions, graph-node transitions,
errors. The admin panel + SQL queries read from this table to answer
"¿qué pasó en este turn?" without relying on ephemeral stdout logs.

See ``trace_recorder.py`` for the main entry point.
"""
