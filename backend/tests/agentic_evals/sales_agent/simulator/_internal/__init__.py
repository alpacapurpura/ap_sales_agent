"""Private namespace — eval simulator internals.

Symbols here are NOT part of the public API (H9). Resto bajo ``simulator/``
top-level (state, actor_profile, result, termination) son public.

T-9 arch fitness gate ``test_simulator_public_api_surface.py`` enforces:
no ``_internal`` symbols leak into ``simulator/__init__.py::__all__``.
"""
