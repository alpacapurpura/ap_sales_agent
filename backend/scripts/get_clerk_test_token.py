#!/usr/bin/env python3
"""Mint a Clerk session JWT for TP testing harness.

Usage:
    .venv/bin/python scripts/get_clerk_test_token.py
    TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)

Reads ``CLERK_SECRET_KEY`` y ``CLERK_TEST_SESSION_ID`` desde ``.env`` (root).
Llama ``POST https://api.clerk.com/v1/sessions/{sid}/tokens`` con Bearer
secret y devuelve el JWT por stdout.

Cache:
    Persiste en ``/tmp/clerk_token_<sid>.cache`` con TTL del JWT decodificado.
    Re-usa el cache si quedan ≥10s para expirar; sino mintea fresh.

Por qué este patrón:
    Clerk default session token TTL = 60s. Las TPs (testing-2026-04 plan)
    corren ~30 turns x ~6s = ~180s mínimo, lejos del TTL. El cache evita
    spam a Clerk BAPI; el refresh automático evita 401 mid-corrida.

NO se commitea token. NO logging del JWT en stdout/stderr más que el
output del propio script (se redirige a $TOKEN var en bash).

Salida:
    stdout = JWT (single line, no trailing newline issues — usar $(...))
    stderr = info logs (tier cache hit/miss, expiry remaining)
    exit 0 = OK | exit 1 = config | exit 2 = HTTP fail
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from urllib import error, request

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

CLERK_BAPI_BASE = "https://api.clerk.com/v1"
CACHE_DIR = Path("/tmp")
TOKEN_REFRESH_BUFFER_S = 10  # refresca si quedan menos que esto


def _b64url_decode(segment: str) -> bytes:
    """Decode a base64url segment (JWT format, no padding)."""
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def _decode_jwt_exp(jwt: str) -> int:
    """Return the JWT's ``exp`` claim (unix epoch seconds)."""
    payload_segment = jwt.split(".")[1]
    payload = json.loads(_b64url_decode(payload_segment))
    return int(payload["exp"])


def _cache_path(session_id: str) -> Path:
    return CACHE_DIR / f"clerk_token_{session_id}.cache"


def _read_cache(session_id: str) -> str | None:
    """Return cached JWT if still valid (≥buffer remaining), else None."""
    cache = _cache_path(session_id)
    if not cache.exists():
        return None
    try:
        jwt = cache.read_text().strip()
        exp = _decode_jwt_exp(jwt)
        remaining = exp - int(time.time())
        if remaining < TOKEN_REFRESH_BUFFER_S:
            print(f"[clerk-token] cache expired ({remaining}s left)", file=sys.stderr)
            return None
        print(f"[clerk-token] cache hit ({remaining}s left)", file=sys.stderr)
        return jwt
    except (OSError, ValueError, IndexError) as exc:
        print(f"[clerk-token] cache read failed: {exc}", file=sys.stderr)
        return None


def _write_cache(session_id: str, jwt: str) -> None:
    cache = _cache_path(session_id)
    try:
        cache.write_text(jwt)
        cache.chmod(0o600)
    except OSError as exc:
        print(f"[clerk-token] cache write failed: {exc}", file=sys.stderr)


def _mint_token(session_id: str, secret_key: str) -> str:
    """POST /v1/sessions/{sid}/tokens — return JWT.

    User-Agent realista requerido: Clerk BAPI corre detrás de Cloudflare,
    que bloquea ``Python-urllib/x.x`` con HTTP 403 (error code 1010).
    """
    url = f"{CLERK_BAPI_BASE}/sessions/{session_id}/tokens"
    req = request.Request(  # noqa: S310 — URL is hardcoded https://api.clerk.com
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
            "User-Agent": "nicolify-tp-harness/1.0 (testing-2026-04)",
        },
        data=b"{}",
    )
    try:
        with request.urlopen(req, timeout=10) as resp:  # noqa: S310 — same as above
            body = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        print(
            f"[clerk-token] HTTP {exc.code} from Clerk BAPI: {body_text[:200]}",
            file=sys.stderr,
        )
        sys.exit(2)
    except error.URLError as exc:
        print(f"[clerk-token] URL error: {exc}", file=sys.stderr)
        sys.exit(2)

    jwt = body.get("jwt")
    if not jwt:
        print(f"[clerk-token] no 'jwt' in response: {body}", file=sys.stderr)
        sys.exit(2)
    return jwt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--session-id",
        default=os.getenv("CLERK_TEST_SESSION_ID"),
        help="Clerk session_id (defaults a $CLERK_TEST_SESSION_ID).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip cache, mint fresh.",
    )
    args = parser.parse_args()

    secret_key = os.getenv("CLERK_SECRET_KEY")
    if not secret_key:
        print("[clerk-token] CLERK_SECRET_KEY no presente en .env", file=sys.stderr)
        sys.exit(1)
    if not args.session_id:
        print(
            "[clerk-token] session_id requerido — pásalo via --session-id o "
            "CLERK_TEST_SESSION_ID env var. Lo extraes del browser con: "
            "window.Clerk.session.id (consola DevTools en dev-app.nicolify.com)",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.no_cache:
        cached = _read_cache(args.session_id)
        if cached:
            sys.stdout.write(cached)
            return

    print("[clerk-token] minting fresh token via Clerk BAPI", file=sys.stderr)
    jwt = _mint_token(args.session_id, secret_key)
    _write_cache(args.session_id, jwt)
    sys.stdout.write(jwt)


if __name__ == "__main__":
    main()
