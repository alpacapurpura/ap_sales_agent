"""Cross-module ARQ workers (F3+).

Owns workers that don't belong to a single bounded context — e.g. the
brand-summary lighthouse regen task fans out from a brand domain event
but writes the per-tenant summary that the *copilot* consumes.
"""
