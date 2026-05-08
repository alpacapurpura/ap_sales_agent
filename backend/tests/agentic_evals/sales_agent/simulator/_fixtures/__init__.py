"""Frozen test fixtures — checked-in artifacts NEVER edited (H10).

Story B (T-9) ships ``golden_v1_simulation_result.yaml`` as the v1 baseline
forward-compat regression anchor. Future schema bumps add NEW frozen
goldens (``golden_v2_*.yaml``) — they MUST coexist with v1 (never replace,
never edit).

Module intentionally empty — fixtures are loaded by file-path, not import.
"""
