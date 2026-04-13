import os
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class ClerkService:
    def __init__(self) -> None:
        self.secret_key = os.getenv("CLERK_SECRET_KEY")
        self.api_url = "https://api.clerk.com/v1"

        if not self.secret_key:
            logger.error("CLERK_SECRET_KEY not set. Clerk integration will fail.")

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Creates a user in Clerk via Backend API.
        Returns the Clerk User Object or raises RuntimeError/ValueError.
        """
        if not self.secret_key:
            msg = "CLERK_SECRET_KEY is missing"
            raise RuntimeError(msg)

        url = f"{self.api_url}/users"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "email_address": [email],
            "password": password,
            "first_name": first_name,
            "skip_password_checks": False,
            "skip_legal_checks": True,
        }

        if last_name:
            payload["last_name"] = last_name

        try:
            logger.info("creating_clerk_user", email=email)
            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        except Exception as e:
            logger.exception("clerk_service_exception")
            msg = f"Error de conexión con Clerk: {e!s}"
            raise RuntimeError(msg) from e

        if response.status_code in {200, 201}:
            return response.json()
        if response.status_code == 422:
            error_detail = response.json().get("errors", [])
            logger.warning(
                "clerk_create_user_failed_validation",
                errors=error_detail,
            )
            if any(e.get("code") == "form_identifier_exists" for e in error_detail):
                msg = "El usuario ya existe en Clerk (form_identifier_exists)."
                raise ValueError(msg)
            if any(e.get("code") == "password_pwned" for e in error_detail):
                msg = "La contraseña es muy común o insegura."
                raise ValueError(msg)

            msg = error_detail[0].get("message") if error_detail else "Datos inválidos"
            msg = f"Error Clerk: {msg}"
            raise ValueError(msg)
        logger.error(
            "clerk_create_user_error",
            status=response.status_code,
            body=response.text,
        )
        msg = f"Error desconocido Clerk ({response.status_code}): {response.text}"
        raise RuntimeError(msg)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        if not self.secret_key:
            return None

        url = f"{self.api_url}/users"
        headers = {"Authorization": f"Bearer {self.secret_key}"}
        params = {"email_address": [email], "limit": 1}

        try:
            response = httpx.get(url, headers=headers, params=params, timeout=5.0)
        except Exception:
            logger.exception("clerk_get_user_error")
            return None
        else:
            if response.status_code == 200:
                users = response.json()
                return users[0] if users else None
        return None

    def update_user_metadata(
        self,
        user_id: str,
        public_metadata: dict[str, Any],
    ) -> bool:
        """
        Updates the user's public metadata (e.g., tenant_id, role).
        This metadata is accessible in the Frontend via Clerk Session.
        """
        if not self.secret_key:
            return False

        url = f"{self.api_url}/users/{user_id}/metadata"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

        payload = {"public_metadata": public_metadata}

        try:
            response = httpx.patch(url, headers=headers, json=payload, timeout=5.0)
        except Exception:
            logger.exception("clerk_metadata_update_exception")
            return False
        else:
            if response.status_code == 200:
                logger.info(
                    "clerk_metadata_updated",
                    user_id=user_id,
                    metadata=public_metadata,
                )
                return True
            logger.error(
                "clerk_metadata_update_failed",
                status=response.status_code,
                body=response.text,
            )
            return False

    def update_user_password(self, user_id: str, password: str) -> bool:
        """
        Updates the user's password.
        """
        if not self.secret_key:
            return False

        url = f"{self.api_url}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

        payload = {"password": password}

        try:
            response = httpx.patch(url, headers=headers, json=payload, timeout=5.0)
        except Exception:
            logger.exception("clerk_password_update_exception")
            return False
        else:
            if response.status_code == 200:
                logger.info("clerk_password_updated", user_id=user_id)
                return True
            logger.error(
                "clerk_password_update_failed",
                status=response.status_code,
                body=response.text,
            )
            return False

    def ban_user(self, user_id: str) -> bool:
        """
        Bans the user.
        """
        if not self.secret_key:
            return False

        url = f"{self.api_url}/users/{user_id}/ban"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(url, headers=headers, timeout=5.0)
        except Exception:
            logger.exception("clerk_user_ban_exception")
            return False
        else:
            if response.status_code == 200:
                logger.info("clerk_user_banned", user_id=user_id)
                return True
            logger.error(
                "clerk_user_ban_failed",
                status=response.status_code,
                body=response.text,
            )
            return False

    def unban_user(self, user_id: str) -> bool:
        """
        Unbans the user.
        """
        if not self.secret_key:
            return False

        url = f"{self.api_url}/users/{user_id}/unban"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(url, headers=headers, timeout=5.0)
        except Exception:
            logger.exception("clerk_user_unban_exception")
            return False
        else:
            if response.status_code == 200:
                logger.info("clerk_user_unbanned", user_id=user_id)
                return True
            logger.error(
                "clerk_user_unban_failed",
                status=response.status_code,
                body=response.text,
            )
            return False

    def delete_user(self, user_id: str) -> bool:
        """
        Deletes the user.
        """
        if not self.secret_key:
            return False

        url = f"{self.api_url}/users/{user_id}"
        headers = {"Authorization": f"Bearer {self.secret_key}"}

        try:
            response = httpx.delete(url, headers=headers, timeout=5.0)
        except Exception:
            logger.exception("clerk_user_delete_exception")
            return False
        else:
            if response.status_code == 200:
                logger.info("clerk_user_deleted", user_id=user_id)
                return True
            logger.error(
                "clerk_user_delete_failed",
                status=response.status_code,
                body=response.text,
            )
            return False
