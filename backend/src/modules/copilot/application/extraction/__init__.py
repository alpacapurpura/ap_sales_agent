"""Copilot extraction application — active-job state + persistence helpers.

Tracks the live URL/document extraction dispatched from inside a copilot
conversation so the orchestrator can pause guided questions while the worker
runs and resume on completion.
"""
