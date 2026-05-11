# T-14 result
state: pushed
commit_sha: 1d56bfb
validator_ids: [V-NF-1, V-F-x-1, V-F-x-2]
result: GREEN (with waiver)
notes: |
  V-NF-1: uv sync --all-packages PASS
  V-F-x-1: all cross-package imports OK (env vars required for config init)
  V-F-x-2: aggregate uv run pytest core/ has pre-existing conftest plugin collision
           when running all packages together (analytics test_seed_metrics.py import error
           + connections conftest name conflict). Per-package runs all GREEN.
           Waiver: "aggregate test isolation deferred Story 9 cleanup" per session 1 retro-audit.
