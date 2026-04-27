"""Pricing layer — resolves provider/model unit costs at a point in time.

Snapshots are fed by ``litellm_sync.sync_pricing`` (daily ARQ task) from
``model_prices_and_context_window.json`` upstream. Resolver is the only
consumer; cost calculator depends on it.
"""
