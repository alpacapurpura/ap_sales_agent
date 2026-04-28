"""Pricing layer — provider/model resolver + daily LiteLLM sync.

* :mod:`aliases` — internal-id → upstream-id translation map.
* :mod:`resolver` — (provider, model, ts) → unit-cost snapshot.
* :mod:`litellm_sync` — daily reconciler against LiteLLM upstream JSON.
"""
