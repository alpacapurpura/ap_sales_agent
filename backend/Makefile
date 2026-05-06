# backend/Makefile — convenience targets for backend-only ops.
#
# Origen: PI-12 S1 Story B T-6 (2026-05-05). Provee atajos para
# operaciones que viven exclusivamente en backend/, sin necesidad de
# subir al Makefile root (que orquesta Docker + frontend + cross-stack).
#
# Native-first (`AGENTS.md`): todos los targets ejecutan en WSL contra
# `backend/.venv/bin/...`. Nunca `docker exec`.
#
# Convivencia con root Makefile: el root continua siendo SSoT para
# `make dev`, `make ci-parity`, `make pytest`, etc. Este Makefile es
# pura conveniencia para targets BE-puros (eval harness, futura
# expansion de smoke targets). Si un target necesita Docker o cross-stack
# vive en el root.

.PHONY: eval-smoke

# PI-12 S1 — sales_agent eval harness smoke runner.
# Corre los 4 escenarios end-to-end de `test_eval_runner_smoke.py` con
# la flag `--run-evals` activada (sin la flag los tests con marker
# `@pytest.mark.eval` quedan SKIPPED — gating de costo, ver T-2 conftest).
#
# Pre-condiciones runtime (las fixtures hacen skip explicito si faltan):
#   - VISIONARIAS_TENANT_ID env var apuntando al UUID del tenant en dev DB
#   - Tenant Visionarias seedeado (`make seed-visionarias` desde root)
#   - LiteLLM proxy activo (`make dev` desde root levanta el stack)
#   - Container brain UP (la fixture `visionarias_tenant_session` hace
#     pytest.skip con razon explicita si la conexion DB falla)
#
# Costo esperado: ~$0.005/run con DeepSeek V4-Flash via LiteLLM proxy.
# Alerta de regresion si supera $0.05/run (ver tabla de assertions Capa 4).
eval-smoke:
	cd $(CURDIR) && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py -v --run-evals
