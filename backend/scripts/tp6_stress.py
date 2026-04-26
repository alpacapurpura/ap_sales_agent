"""TP6 stress S6.18 SMS length + S6.19 WA markdown clean.

10 prompts each. Confirms the sanitizer enforcement holds across diverse
content under both real SSE flow + post-sanitization.
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
TENANT = "c67c9845-6cf7-4aee-beba-7e177e84d167"
ENDPOINT = "http://localhost:8000/api/v1/copilot/chat"

MD_NOISE_RE = re.compile(r"\*\*[^*]+\*\*|`{3,}|\[[^\]]+\]\([^)]+\)|^#{1,6}\s+", re.MULTILINE)

SMS_PROMPTS = [
    "Armame un SMS para promo flash de 24 horas en cursos online",
    "Armame un SMS confirmando reserva de webinar de marketing",
    "Armame un SMS de recordatorio de pago vencido",
    "Armame un SMS para invitar a sesion de mentoria gratuita",
    "Armame un SMS de bienvenida a nuevo suscriptor del boletin",
    "Armame un SMS para anunciar lanzamiento de nueva oferta de coaching",
    "Armame un SMS para encuesta NPS de un cliente reciente",
    "Armame un SMS celebrando 1000 ventas en el ecommerce",
    "Armame un SMS de upsell post-compra ofreciendo curso premium",
    "Armame un SMS reactivando carrito abandonado",
]

WA_PROMPTS = [
    "Armame un mensaje para WhatsApp invitando a webinar gratuito de marketing",
    "Armame un mensaje para WhatsApp anunciando promo Black Friday 50% OFF",
    "Armame un mensaje para WhatsApp dando seguimiento a un lead frio",
    "Armame un mensaje para WhatsApp confirmando inscripcion a curso online",
    "Armame un mensaje para WhatsApp pidiendo testimonio post-compra",
    "Armame un mensaje para WhatsApp ofreciendo descuento por referido",
    "Armame un mensaje para WhatsApp anunciando nuevo episodio de podcast",
    "Armame un mensaje para WhatsApp invitando a sesion estrategica gratuita",
    "Armame un mensaje para WhatsApp anunciando cierre de inscripciones",
    "Armame un mensaje para WhatsApp respondiendo a consulta de precios",
]


def get_token() -> str:
    import subprocess

    out = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/get_clerk_test_token.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in out.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("[clerk-token]"):
            return line
    raise RuntimeError(out.stdout)


async def run_one(client: httpx.AsyncClient, prompt: str, token: str) -> dict:
    body = {
        "message": prompt,
        "conversation_id": None,
        "blocks": None,
        "context": {"current_route": "/brand-studio", "locale": "es"},
    }
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT,
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream",
    }
    text = ""
    err = None
    t0 = time.perf_counter()
    try:
        async with client.stream("POST", ENDPOINT, json=body, headers=headers, timeout=60.0) as r:
            if r.status_code != 200:
                return {"prompt": prompt, "error": f"http_{r.status_code}", "len": 0}
            event_name = None
            async for raw in r.aiter_lines():
                line = raw.strip()
                if not line:
                    event_name = None
                    continue
                if line.startswith("event:"):
                    event_name = line.split(":", 1)[1].strip()
                    continue
                if line.startswith("data:"):
                    try:
                        data = json.loads(line.split(":", 1)[1].strip())
                    except json.JSONDecodeError:
                        continue
                    if event_name == "block_end":
                        block = data.get("final") or {}
                        if block.get("type") == "text":
                            text = block.get("markdown") or text
                    elif event_name == "done":
                        break
    except (httpx.HTTPError, asyncio.TimeoutError) as exc:
        err = str(exc)[:120]
    return {
        "prompt": prompt,
        "output": text.strip(),
        "len": len(text.strip()),
        "latency_ms": int((time.perf_counter() - t0) * 1000),
        "error": err,
    }


async def main() -> None:
    token = get_token()
    token_ts = time.time()
    timeout = httpx.Timeout(60.0, read=60.0)
    sms_results, wa_results = [], []
    async with httpx.AsyncClient(timeout=timeout) as client:
        print("=== S6.18 SMS x10 ===")
        for p in SMS_PROMPTS:
            if time.time() - token_ts > 40:
                token = get_token()
                token_ts = time.time()
            r = await run_one(client, p, token)
            sms_results.append(r)
            mark = "✅" if r.get("len", 0) <= 160 and not r.get("error") else "❌"
            print(f"{mark} len={r.get('len', 0):3d} {r.get('error') or 'ok':20s}")

        print("\n=== S6.19 WA x10 ===")
        for p in WA_PROMPTS:
            if time.time() - token_ts > 40:
                token = get_token()
                token_ts = time.time()
            r = await run_one(client, p, token)
            md_hits = MD_NOISE_RE.findall(r.get("output") or "")
            r["md_hits"] = md_hits
            wa_results.append(r)
            mark = "✅" if not md_hits and not r.get("error") else "❌"
            print(f"{mark} len={r.get('len', 0):4d} md_noise={len(md_hits)} {r.get('error') or 'ok'}")

    sms_pass = sum(1 for r in sms_results if not r.get("error") and r.get("len", 0) <= 160)
    wa_pass = sum(1 for r in wa_results if not r.get("error") and not r.get("md_hits"))
    print(f"\nSMS pass: {sms_pass}/10  WA pass: {wa_pass}/10")
    out = {"sms": sms_results, "wa": wa_results}
    Path(ROOT / "tp6_stress_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
