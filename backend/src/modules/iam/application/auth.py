"""Auth application layer."""

import logging
import os

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Configure Logger
logger = logging.getLogger(__name__)

# Configura esto en tu .env
# Ej: `https://clerk.your-domain.com` o `https://polished-poodle-12.clerk.accounts.dev`
CLERK_ISSUER = os.getenv("CLERK_ISSUER")

if not CLERK_ISSUER:
    logger.warning("CLERK_ISSUER not set in environment. JWT verification will fail.")

JWKS_URL = f"{CLERK_ISSUER}/.well-known/jwks.json"

security = HTTPBearer()

# Cachear las llaves públicas para no pedirlas en cada request
try:
    jwks_client = jwt.PyJWKClient(JWKS_URL)
except Exception as e:  # noqa: BLE001 — service resilience
    logger.warning("Could not initialize JWKS client: %s", e)
    jwks_client = None


def verify_token_payload(token: str) -> dict:
    """Core verification logic, independent of FastAPI Depends."""
    if not CLERK_ISSUER:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: CLERK_ISSUER missing",
        )

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            # Audience check can be tricky with Clerk dev keys, often safe to skip in dev or set explicitly
            options={"verify_aud": False},
            leeway=60,  # Add 60s leeway for clock skew
        )
    except jwt.exceptions.PyJWTError as e:
        logger.exception("JWT Validation Error")
        raise HTTPException(status_code=401, detail=f"Invalid Token: {e!s}") from e
    except Exception as e:
        logger.exception("Token Verification Error")
        raise HTTPException(
            status_code=401,
            detail="Could not verify credentials",
        ) from e

    else:
        return payload


def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """Verify the Bearer Token extracted from the Authorization header against Clerk's JWKS."""
    return verify_token_payload(credentials.credentials)
