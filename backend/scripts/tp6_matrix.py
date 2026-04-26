"""TP6 matrix runner — channel formatter validation.

Runs 16 (channel × content) chat scenarios + S6.18 SMS length + S6.19 WA
markdown clean against /copilot/chat live with Visionarias / alpaca-2 tenant
on /brand-studio route (lighthouse injected).

Captures: turn_id, final assistant text, latency_ms, tool_calls list. Then
post-processes regex checks (voseo / WA markdown noise / SMS length) and
writes JSON report to tp6_matrix_results.json.
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
TENANT_ALPACA = "c67c9845-6cf7-4aee-beba-7e177e84d167"  # has brand_summary v2
ROUTE = "/brand-studio"  # lighthouse-injected route
ENDPOINT = "http://localhost:8000/api/v1/copilot/chat"

VOSEO_RE = re.compile(
    r"\b(vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|"
    r"poné|usá|hacé|elegí|seleccioná|arrancá|empezá|agregá|configurá|"
    r"revisá|escribí|guardá|subí|bajá|abrí|volvé|andá|cambiá|ofrecés|"
    r"cobrás|ejecutás|acompañás|activás|desactivás|linkeá|despublicala|"
    r"cancelala|validá|considerá|formulala|marcá|referís|atendés|integrás|"
    r"listá|probá|mostrá|compartí|contá|explicá|fijate|acordate)\b",
    re.IGNORECASE,
)

# Standard markdown noise that shouldn't appear in WhatsApp output.
MD_NOISE_RE = re.compile(r"\*\*[^*]+\*\*|`{3,}|\[[^\]]+\]\([^)]+\)|^#{1,6}\s+", re.MULTILINE)

CONTENT_TYPES = {
    "headline": "un headline impactante para promo de cursos online de marketing",
    "email": "un email de bienvenida tras suscripción al boletín de marketing",
    "story": "una historia corta (≤4 frases) sobre cómo nuestro cliente Juan triplicó ventas con automatización",
    "cta": "un CTA para invitar al webinar gratuito de embudos de venta del jueves",
}

CHANNELS = ["chat", "whatsapp", "email", "sms"]


def get_token() -> str:
    import subprocess

    result = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/get_clerk_test_token.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("[clerk-token]"):
            return line
    raise RuntimeError(f"no token in output: {result.stdout!r}")


async def run_scenario(
    client: httpx.AsyncClient,
    sid: str,
    prompt: str,
    channel: str,
    token: str,
    tenant: str,
) -> dict:
    body = {
        "message": prompt,
        "conversation_id": None,
        "blocks": None,
        "context": {"current_route": ROUTE, "locale": "es"},
    }
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenant,
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream",
    }

    accumulated_text = ""
    turn_id: str | None = None
    conv_id: str | None = None
    tool_calls: list[str] = []
    error: str | None = None
    t0 = time.perf_counter()

    try:
        async with client.stream("POST", ENDPOINT, json=body, headers=headers, timeout=60.0) as resp:
            if resp.status_code != 200:
                err_body = await resp.aread()
                error = f"http_{resp.status_code}: {err_body[:300].decode(errors='replace')}"
                return {
                    "id": sid,
                    "channel": channel,
                    "prompt": prompt,
                    "error": error,
                    "latency_ms": int((time.perf_counter() - t0) * 1000),
                }
            event_name = None
            async for raw_line in resp.aiter_lines():
                line = raw_line.strip()
                if not line:
                    event_name = None
                    continue
                if line.startswith("event:"):
                    event_name = line.split(":", 1)[1].strip()
                    continue
                if line.startswith("data:"):
                    payload_raw = line.split(":", 1)[1].strip()
                    try:
                        payload = json.loads(payload_raw)
                    except json.JSONDecodeError:
                        continue
                    if event_name == "message_start":
                        turn_id = payload.get("message_id") or payload.get("turn_id") or turn_id
                        conv_id = payload.get("conversation_id") or conv_id
                    elif event_name == "block_delta":
                        delta = payload.get("delta") or {}
                        if isinstance(delta, dict):
                            accumulated_text += delta.get("markdown") or delta.get("text") or ""
                        elif isinstance(delta, str):
                            accumulated_text += delta
                    elif event_name == "block_end":
                        # block_end emits the SANITIZED final block — use it
                        # over the raw accumulated delta stream (which is
                        # pre-sanitize). Schema: data.final.markdown.
                        block = payload.get("final") or payload.get("block") or {}
                        if block.get("type") == "text":
                            content = block.get("markdown") or block.get("content") or block.get("text") or ""
                            if content:
                                accumulated_text = content
                    elif event_name == "tool_start":
                        name = payload.get("name") or payload.get("tool_name")
                        if name:
                            tool_calls.append(name)
                    elif event_name == "error":
                        error = json.dumps(payload)[:300]
                    elif event_name == "done":
                        break
    except (httpx.HTTPError, asyncio.TimeoutError) as exc:
        error = f"transport: {exc!r}"

    latency_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "id": sid,
        "channel": channel,
        "prompt": prompt,
        "turn_id": turn_id,
        "conversation_id": conv_id,
        "tool_calls": tool_calls,
        "output": accumulated_text.strip(),
        "len_chars": len(accumulated_text.strip()),
        "latency_ms": latency_ms,
        "error": error,
    }


def post_validate(scenario: dict) -> dict:
    out = scenario.get("output") or ""
    checks = {
        "voseo_hits": VOSEO_RE.findall(out),
        "md_noise_hits": MD_NOISE_RE.findall(out),
        "len_chars": len(out),
        "exceeds_sms_160": scenario["channel"] == "sms" and len(out) > 160,
        "wa_has_md_noise": scenario["channel"] == "whatsapp" and bool(MD_NOISE_RE.search(out)),
    }
    return {**scenario, "checks": checks}


async def main() -> None:
    token = get_token()
    token_ts = time.time()
    print(f"Token obtained ({len(token)} chars)")

    scenarios: list[tuple[str, str, str]] = []
    sid = 1
    for channel in CHANNELS:
        for ct_label, ct_prompt in CONTENT_TYPES.items():
            sid_str = f"S6.{sid}"
            prompt = (
                f"Armame {ct_prompt}, formateado para enviar por {channel}. "
                "Respondé directamente con el texto listo para copiar (sin explicaciones)."
            )
            scenarios.append((sid_str, channel, prompt))
            sid += 1

    results: list[dict] = []
    timeout = httpx.Timeout(60.0, read=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for s_id, channel, prompt in scenarios:
            # Refresh token if older than 40s (Clerk JWT expires at 60s).
            if time.time() - token_ts > 40:
                token = get_token()
                token_ts = time.time()
                print(f"  [token refreshed]")
            print(f"\n{s_id} [{channel}] starting...")
            result = await run_scenario(client, s_id, prompt, channel, token, TENANT_ALPACA)
            result = post_validate(result)
            results.append(result)
            err = result.get("error")
            if err:
                print(f"  ERROR: {err}")
            else:
                print(
                    f"  ok | len={result['len_chars']} latency={result['latency_ms']}ms "
                    f"tools={result['tool_calls']} voseo={len(result['checks']['voseo_hits'])} "
                    f"md_noise={len(result['checks']['md_noise_hits'])}"
                )

    out_path = ROOT / "tp6_matrix_results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nResults written to {out_path}")

    pass_count = sum(1 for r in results if not r.get("error"))
    print(f"\nSummary: {pass_count}/{len(results)} completed without HTTP/transport error")
    voseo_total = sum(len(r["checks"]["voseo_hits"]) for r in results if not r.get("error"))
    sms_overflows = sum(1 for r in results if r["checks"]["exceeds_sms_160"])
    wa_md_noise = sum(1 for r in results if r["checks"]["wa_has_md_noise"])
    print(f"  voseo hits: {voseo_total}")
    print(f"  sms >160 chars: {sms_overflows}")
    print(f"  wa with md noise: {wa_md_noise}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
