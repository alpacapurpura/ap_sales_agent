"""Arch gate — Cost bucket separation para goldens generation (Story D / T-3).

Verifica que la generación de candidatos goldens escriba SOLO a
eval_simulator_llm_call (Story B H6/H7 cement) y NO contamine la tabla
de producción copilot_llm_call.

Gate gateado con variable de entorno EVAL_GOLDENS_COST_BUCKET_VERIFY=1
(CI nightly opt-in) porque requiere:
  - Base de datos PostgreSQL accesible
  - Story B run_simulation funcionando (LLM calls reales)
  - Costo estimado ~$0.22 (3 celdas x 1 run)

Invariantes verificados:
  - ≥3 nuevas filas en eval_simulator_llm_call post-generación
  - CERO nuevas filas en copilot_llm_call post-generación
  - Costo bucket separation Story B H6/H7
"""

from __future__ import annotations

import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Gate: solo CI nightly cuando EVAL_GOLDENS_COST_BUCKET_VERIFY=1
pytestmark = pytest.mark.skipif(
    not os.environ.get("EVAL_GOLDENS_COST_BUCKET_VERIFY"),
    reason="Cost-bucket invariant verification requiere EVAL_GOLDENS_COST_BUCKET_VERIFY=1 "
    "(CI nightly opt-in — costo LLM ~$0.22 por ejecución). "
    "Activar: EVAL_GOLDENS_COST_BUCKET_VERIFY=1 pytest ...",
)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]  # backend/
sys.path.insert(0, str(_BACKEND_ROOT / "scripts"))


@pytest.fixture
def _db_session():
    """SQLAlchemy session para consultas DB post-generación.

    Importa lazily para evitar errores de conexión cuando el gate está skipped.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from src.core.config import settings

    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    with Session(engine) as session:
        yield session


def _count_eval_simulator_llm_call(session: object, min_created_at: object) -> int:
    """Cuenta filas en eval_simulator_llm_call creadas después de min_created_at."""
    from sqlalchemy import text

    result = session.execute(
        text("SELECT COUNT(*) FROM eval_simulator_llm_call WHERE created_at > :min_created_at"),
        {"min_created_at": min_created_at},
    )
    return result.scalar_one()


def _count_copilot_llm_call(session: object, min_created_at: object) -> int:
    """Cuenta filas en copilot_llm_call creadas después de min_created_at."""
    from sqlalchemy import text

    result = session.execute(
        text("SELECT COUNT(*) FROM copilot_llm_call WHERE created_at > :min_created_at"),
        {"min_created_at": min_created_at},
    )
    return result.scalar_one()


class TestGoldensCostBucketInvariant:
    """Verifica que la generación de goldens no contamine tablas de producción."""

    def test_generation_writes_only_to_eval_bucket(self, _db_session: object, tmp_path: Path) -> None:
        """Generación de 3 simulaciones (1 tenant x 3 kinds x 1 run) debe:
        - Escribir ≥3 filas en eval_simulator_llm_call
        - Escribir CERO filas en copilot_llm_call
        """
        from datetime import UTC, datetime

        import generate_golden_candidates as _gen

        # Timestamp de referencia: filas creadas DESPUÉS de este momento
        cutoff_time = datetime.now(tz=UTC)

        # Correr generación con 1 run por celda, solo tenant_coach_lat (3 celdas)
        exit_code = asyncio.run(
            _gen._main_async(
                runs_per_cell=1,
                concurrency=3,
                cost_budget_usd=Decimal("8.00"),
                output_dir=tmp_path,
                run_id="cost-bucket-test",
                seed_base=42,
                tenant_filter="tenant_coach_lat",
                persona_kind_filter=None,  # happy + nurture + unqualified = 3 celdas
            )
        )

        assert exit_code in (0, 1), (
            f"Generación devolvió exit_code={exit_code} (esperado 0 o 1, no 2 = budget overflow)"
        )

        # Verificar que se escribieron rows en el bucket correcto
        eval_rows = _count_eval_simulator_llm_call(_db_session, cutoff_time)
        copilot_rows = _count_copilot_llm_call(_db_session, cutoff_time)

        assert eval_rows >= 3, (
            f"Se esperaban ≥3 filas en eval_simulator_llm_call post-generación, "
            f"se encontraron {eval_rows}. "
            f"Verificar Story B H6/H7 cost-bucket separation cement."
        )

        assert copilot_rows == 0, (
            f"INVARIANTE VIOLADO (Story B H6/H7): se encontraron {copilot_rows} "
            f"filas nuevas en copilot_llm_call post-generación de goldens. "
            f"La generación NO debe escribir en tablas de producción. "
            f"Verificar que run_simulation use eval_simulator LLM call recorder."
        )
