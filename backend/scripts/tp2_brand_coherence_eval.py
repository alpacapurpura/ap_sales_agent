"""TP2 S2.3 — drive 10 brand-coherence prompts + judge each.

Sends prompts spaced 40s apart against ``/api/v1/copilot/chat`` to keep
under the OpenAI tier-1 TPM constraint observed in TP1 (B2). Captures the
streamed assistant text, then hits ``CopilotJudge`` (real LLM) to score
each pair on ``brand_coherence`` + ``tone`` against the persisted
``brand_summary`` for the alpaca-2 tenant.

Run from ``backend/`` with ARQ + worker + dev API up, OPENAI_API_KEY in
the env, and a fresh Clerk token cached.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib import error, request
from uuid import UUID

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

API_BASE = os.environ.get("TP2_API_BASE", "http://localhost:8000")
TENANT_ID = os.environ.get("TP2_TENANT_ID", "c67c9845-6cf7-4aee-beba-7e177e84d167")
ROUTE = os.environ.get("TP2_ROUTE", "/offer-studio")
SPACING_SECONDS = int(os.environ.get("TP2_SPACING_S", "40"))

PROMPTS: tuple[str, ...] = (
    "dame ideas de contenido para esta semana",
    "cómo mejoro mi headline",
    "escribime un email de bienvenida para nuevos suscriptores",
    "qué tono debo usar en mi nueva landing",
    "dame 3 ideas de stories",
    "armame el copy de un anuncio Meta",
    "qué le respondo a un cliente que me dice 'está caro'",
    "cómo posiciono mi nueva oferta",
    "dame el outline de un reel viral",
    "armá un caption corto para Instagram",
)


def _clerk_token() -> str:
    """Mint or reuse the cached Clerk JWT (mint per turn — Clerk TTL=60s)."""
    import subprocess

    venv_python = REPO_ROOT / "backend" / ".venv" / "bin" / "python"
    helper = REPO_ROOT / "backend" / "scripts" / "get_clerk_test_token.py"
    out = subprocess.run(
        [str(venv_python), str(helper)],
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout.strip()


def _send_turn(token: str, message: str, *, conv_id: str | None) -> tuple[str, str]:
    """POST one chat turn; return (assistant_text, conversation_id)."""
    payload = json.dumps(
        {
            "message": message,
            "conversation_id": conv_id,
            "client_context": {"current_route": ROUTE},
        },
    ).encode("utf-8")

    req = request.Request(  # noqa: S310 — local URL only
        f"{API_BASE}/api/v1/copilot/chat",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID,
            "Authorization": f"Bearer {token}",
        },
    )

    text_parts: list[str] = []
    captured_conv_id = conv_id
    captured_message_id: str | None = None
    try:
        with request.urlopen(req, timeout=120) as resp:  # noqa: S310
            buffer = b""
            for chunk in resp:
                buffer += chunk
                while b"\n\n" in buffer:
                    raw_event, buffer = buffer.split(b"\n\n", 1)
                    event_lines = raw_event.decode("utf-8", errors="replace").splitlines()
                    event_name = ""
                    data_str = ""
                    for line in event_lines:
                        if line.startswith("event:"):
                            event_name = line[len("event:") :].strip()
                        elif line.startswith("data:"):
                            data_str = line[len("data:") :].strip()
                    if not data_str:
                        continue
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    if event_name == "block_delta":
                        delta = (data.get("delta") or {}).get("markdown") or ""
                        text_parts.append(delta)
                    elif event_name == "message_start":
                        captured_message_id = data.get("message_id")
                    elif event_name in {"conversation_meta", "conversation"}:
                        captured_conv_id = data.get("conversation_id") or captured_conv_id
    except error.HTTPError as exc:
        print(f"[tp2] HTTPError {exc.code}: {exc.read()[:500]!r}", file=sys.stderr)
        raise

    text = "".join(text_parts).strip()
    return text, captured_conv_id or captured_message_id or "?"


def _resolve_conv_id_from_db(tenant_id: str, after_iso: str) -> str | None:
    """Fall back to the latest copilot_trace_event row when SSE didn't surface conv id."""
    import subprocess

    sql = (
        "SELECT conversation_id::text FROM copilot_trace_event "
        f"WHERE tenant_id='{tenant_id}' AND event_type='turn_end' "
        f"AND created_at >= '{after_iso}' "
        "ORDER BY created_at DESC LIMIT 1;"
    )
    out = subprocess.run(
        [
            "docker",
            "exec",
            "visionarias_postgres",
            "psql",
            "-U",
            "postgres",
            "-d",
            "visionarias_logs",
            "-tAc",
            sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout.strip() or None


def _judge(brand_summary: str, results: list[dict[str, str]]) -> list[dict[str, object]]:
    """Run CopilotJudge against each (prompt, response) pair."""
    import importlib

    main = importlib.import_module("src.main")  # noqa: F841 — boot side effect for mappers
    from sqlalchemy.orm import configure_mappers

    configure_mappers()

    from src.modules.copilot.application.observability.judge import CopilotJudge

    judge = CopilotJudge(threshold=4.0)
    out: list[dict[str, object]] = []
    for row in results:
        result = judge.evaluate(
            user_input=row["prompt"],
            assistant_output=row["response"],
            brand_summary=brand_summary,
            context=f"current_route={ROUTE}",
        )
        out.append(
            {
                "prompt": row["prompt"],
                "response_preview": row["response"][:160],
                "avg": result.avg_score,
                "brand_coherence": next((d.score for d in result.dimensions if d.name == "brand_coherence"), None),
                "tone": next((d.score for d in result.dimensions if d.name == "tone"), None),
                "utility": next((d.score for d in result.dimensions if d.name == "utility"), None),
                "accuracy": next((d.score for d in result.dimensions if d.name == "accuracy"), None),
                "passes_threshold": result.passes_threshold,
            },
        )
    return out


def _load_brand_summary() -> str:
    """Read the persisted brand summary for ``TENANT_ID`` via SQLAlchemy.

    Inside the container we can't shell out to ``docker exec``, so we hit
    Postgres directly via the same engine the API uses.
    """
    import importlib

    importlib.import_module("src.main")  # boot mappers
    from sqlalchemy.orm import configure_mappers

    configure_mappers()

    from sqlalchemy import select

    from src.core.database import SessionLocal
    from src.modules.brand.infrastructure.models.brand_summary_model import (
        BrandSummaryModel,
    )

    with SessionLocal() as db:
        row = db.execute(
            select(BrandSummaryModel).where(
                BrandSummaryModel.tenant_id == UUID(TENANT_ID),
            ),
        ).scalar_one_or_none()
        return row.summary if row else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("drive", "judge"), default="drive")
    parser.add_argument("--responses-file", default="/tmp/tp2_responses.json")
    args = parser.parse_args()

    if args.mode == "drive":
        rows: list[dict[str, str]] = []
        conv_id: str | None = None
        for idx, prompt in enumerate(PROMPTS, 1):
            if idx > 1:
                time.sleep(SPACING_SECONDS)
            token = _clerk_token()  # Clerk default TTL=60s — refresh per turn
            t0 = time.time()
            text, conv_id_out = _send_turn(token, prompt, conv_id=conv_id)
            elapsed = time.time() - t0
            print(f"[tp2] {idx:02d}/{len(PROMPTS)} {elapsed:6.1f}s len={len(text):4d} conv={conv_id_out[:8]}")
            print(f"      prompt: {prompt}")
            print(f"      preview: {text[:120]!r}")
            rows.append({"prompt": prompt, "response": text, "conv_id": conv_id_out, "elapsed_s": str(elapsed)})
            if conv_id is None:
                conv_id = conv_id_out  # share conversation across turns
        Path(args.responses_file).write_text(json.dumps(rows, ensure_ascii=False, indent=2))
        print(f"[tp2] wrote {args.responses_file}")
        return 0

    # judge mode
    rows = json.loads(Path(args.responses_file).read_text())
    brand_summary = _load_brand_summary()
    print(f"[tp2] brand_summary len={len(brand_summary)}")
    judged = _judge(brand_summary, rows)

    bc_scores = [j["brand_coherence"] for j in judged if j["brand_coherence"] is not None]
    tone_scores = [j["tone"] for j in judged if j["tone"] is not None]
    avg_bc = sum(bc_scores) / len(bc_scores) if bc_scores else 0.0
    avg_tone = sum(tone_scores) / len(tone_scores) if tone_scores else 0.0
    avg_overall = sum(j["avg"] for j in judged) / len(judged) if judged else 0.0
    print()
    print(f"{'#':>2} {'avg':>4} {'bc':>3} {'tone':>4} {'util':>4} {'acc':>3}  prompt")
    for i, j in enumerate(judged, 1):
        bc = j["brand_coherence"] or "-"
        tone = j["tone"] or "-"
        util = j["utility"] or "-"
        acc = j["accuracy"] or "-"
        print(f"{i:>2} {j['avg']:>4.2f} {bc:>3} {tone:>4} {util:>4} {acc:>3}  {j['prompt'][:60]}")
    print()
    print(f"avg brand_coherence : {avg_bc:.2f}  (target ≥4.0  hard fail <3.0)")
    print(f"avg tone            : {avg_tone:.2f}  (target ≥4.0  voseo = hard fail)")
    print(f"avg overall (4 dim) : {avg_overall:.2f}")

    Path("/tmp/tp2_judged.json").write_text(json.dumps(judged, ensure_ascii=False, indent=2))
    print("[tp2] judged dump → /tmp/tp2_judged.json")

    return 0 if avg_bc >= 4.0 and avg_tone >= 4.0 else 2


if __name__ == "__main__":
    sys.exit(main())
