"""Bootstrap module — registers every agent's observability spec.

Importing this module imports each agent's ``observability/__init__.py``,
which in turn calls ``register_agent_observability(...)``. After the
import the cross-agent registry is fully populated.

**Every entrypoint that uses cross-agent observability must import this
module:**

* ``main.py``       (FastAPI app)
* ``admin/app.py``  (Streamlit admin)
* Worker ``on_startup`` callbacks (ARQ workers / schedulers)

The dependency points: ``shared/agent_observability/registry.py`` (pure)
← ``modules/*/observability/__init__.py`` (calls register) ← *this
bootstrap* (pulls in both agents) ← entrypoints.

This file lives in ``shared/infrastructure/`` because
``shared/agent_observability/`` is purity-tested (no
``src.modules.*`` imports). ``shared/infrastructure/`` is the existing
home for the same pattern (see :mod:`model_registry`).
"""

# Each import triggers the agent's observability __init__ to call
# register_agent_observability(...).  noqa: F401 — imports are
# side-effect only.
from src.modules.campaigns import observability as _campaigns_observability  # noqa: F401
from src.modules.copilot import observability as _copilot_observability  # noqa: F401
from src.modules.sales_agent import observability as _sales_agent_observability  # noqa: F401
from src.modules.sales_agent.observability.eval_simulator import spec as _eval_simulator_observability  # noqa: F401
