import os
import httpx
import structlog
from typing import Optional, Dict, Any, List

logger = structlog.get_logger()

class ClerkService:
    def __init__(self):
        self.secret_key = os.getenv("CLERK_SECRET_KEY")
        self.api_url = "https://api.clerk.com/v1"
        
        if not self.secret_key:
            logger.error("CLERK_SECRET_KEY not set. Clerk integration will fail.")

    def create_user(self, email: str, password: str, first_name: str, last_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a user in Clerk via Backend API.
        Returns the Clerk User Object or raises Exception.
        """
        if not self.secret_key:
            raise Exception("CLERK_SECRET_KEY is missing")

        url = f"{self.api_url}/users"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "email_address": [email],
            "password": password,
            "first_name": first_name,
            "skip_password_checks": False,
            "skip_legal_checks": True
        }
        
        if last_name:
            payload["last_name"] = last_name

        try:
            logger.info("creating_clerk_user", email=email)
            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
            
            if response.status_code == 200: # Clerk returns 200 OK for user creation often, but docs say 200 or 201
                return response.json()
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 422:
                # Often means user already exists or password too weak
                error_detail = response.json().get("errors", [])
                logger.warning("clerk_create_user_failed_validation", errors=error_detail)
                # Check if it's "form_identifier_exists"
                if any(e.get("code") == "form_identifier_exists" for e in error_detail):
                     raise Exception("El usuario ya existe en Clerk (form_identifier_exists).")
                if any(e.get("code") == "password_pwned" for e in error_detail):
                     raise Exception("La contraseña es muy común o insegura.")
                     
                msg = error_detail[0].get('message') if error_detail else "Datos inválidos"
                raise Exception(f"Error Clerk: {msg}")
            else:
                logger.error("clerk_create_user_error", status=response.status_code, body=response.text)
                raise Exception(f"Error desconocido Clerk ({response.status_code}): {response.text}")
                
        except Exception as e:
            # Re-raise explicit exceptions
            if "El usuario ya existe" in str(e):
                raise e
            logger.error("clerk_service_exception", error=str(e))
            raise Exception(f"Error de conexión con Clerk: {str(e)}")

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if not self.secret_key:
            return None
        
        url = f"{self.api_url}/users"
        headers = {"Authorization": f"Bearer {self.secret_key}"}
        params = {"email_address": [email], "limit": 1}
        
        try:
            response = httpx.get(url, headers=headers, params=params, timeout=5.0)
            if response.status_code == 200:
                users = response.json()
                return users[0] if users else None
        except Exception as e:
            logger.error("clerk_get_user_error", error=str(e))
            return None

    def update_user_metadata(self, user_id: str, public_metadata: Dict[str, Any]) -> bool:
        """
        Updates the user's public metadata (e.g., tenant_id, role).
        This metadata is accessible in the Frontend via Clerk Session.
        """
        if not self.secret_key:
            return False

        url = f"{self.api_url}/users/{user_id}/metadata"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "public_metadata": public_metadata
        }

        try:
            response = httpx.patch(url, headers=headers, json=payload, timeout=5.0)
            if response.status_code == 200:
                logger.info("clerk_metadata_updated", user_id=user_id, metadata=public_metadata)
                return True
            else:
                logger.error("clerk_metadata_update_failed", status=response.status_code, body=response.text)
                return False
        except Exception as e:
            logger.error("clerk_metadata_update_exception", error=str(e))
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
            "Content-Type": "application/json"
        }
        
        payload = {
            "password": password
        }

        try:
            response = httpx.patch(url, headers=headers, json=payload, timeout=5.0)
            if response.status_code == 200:
                logger.info("clerk_password_updated", user_id=user_id)
                return True
            else:
                logger.error("clerk_password_update_failed", status=response.status_code, body=response.text)
                return False
        except Exception as e:
            logger.error("clerk_password_update_exception", error=str(e))
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
            "Content-Type": "application/json"
        }

        try:
            response = httpx.post(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                logger.info("clerk_user_banned", user_id=user_id)
                return True
            else:
                logger.error("clerk_user_ban_failed", status=response.status_code, body=response.text)
                return False
        except Exception as e:
            logger.error("clerk_user_ban_exception", error=str(e))
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
            "Content-Type": "application/json"
        }

        try:
            response = httpx.post(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                logger.info("clerk_user_unbanned", user_id=user_id)
                return True
            else:
                logger.error("clerk_user_unban_failed", status=response.status_code, body=response.text)
                return False
        except Exception as e:
            logger.error("clerk_user_unban_exception", error=str(e))
            return False

    # ==================== Organization Methods ====================

    def create_organization(self, name: str, slug: str) -> Optional[Dict[str, Any]]:
        """Creates a Clerk Organization. Returns the org object or None."""
        if not self.secret_key:
            raise Exception("CLERK_SECRET_KEY is missing")

        url = f"{self.api_url}/organizations"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        payload = {"name": name}

        try:
            logger.info("creating_clerk_organization", name=name, slug=slug)
            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
            if response.status_code in (200, 201):
                org = response.json()
                logger.info("clerk_organization_created", org_id=org.get("id"), slug=slug)
                return org
            elif response.status_code == 422:
                error_detail = response.json().get("errors", [])
                # Slug already taken — try to find existing org
                if any(e.get("code") == "form_identifier_exists" for e in error_detail):
                    logger.warning("clerk_org_slug_exists", slug=slug)
                    existing = self.get_organization_by_slug(slug)
                    if existing:
                        return existing
                msg = error_detail[0].get("message") if error_detail else "Datos inválidos"
                raise Exception(f"Error Clerk Org: {msg}")
            else:
                logger.error("clerk_create_org_error", status=response.status_code, body=response.text)
                raise Exception(f"Error Clerk Org ({response.status_code}): {response.text}")
        except Exception as e:
            if "Error Clerk Org" in str(e):
                raise
            logger.error("clerk_create_org_exception", error=str(e))
            raise Exception(f"Error de conexión con Clerk (org): {str(e)}")

    def get_organization_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetches a Clerk Organization by slug."""
        if not self.secret_key:
            return None

        url = f"{self.api_url}/organizations"
        headers = {"Authorization": f"Bearer {self.secret_key}"}
        params = {"query": slug, "limit": 10}

        try:
            response = httpx.get(url, headers=headers, params=params, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                orgs = data.get("data", data) if isinstance(data, dict) else data
                for org in orgs:
                    if org.get("slug") == slug:
                        return org
            return None
        except Exception as e:
            logger.error("clerk_get_org_by_slug_error", error=str(e))
            return None

    def add_member_to_organization(self, org_id: str, user_id: str, role: str = "org:member") -> bool:
        """Adds a user to a Clerk Organization."""
        if not self.secret_key:
            return False

        url = f"{self.api_url}/organizations/{org_id}/memberships"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        payload = {"user_id": user_id, "role": role}

        try:
            logger.info("adding_clerk_org_member", org_id=org_id, user_id=user_id, role=role)
            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
            if response.status_code in (200, 201):
                logger.info("clerk_org_member_added", org_id=org_id, user_id=user_id)
                return True
            elif response.status_code == 422:
                # User might already be a member
                error_detail = response.json().get("errors", [])
                if any("already" in e.get("message", "").lower() for e in error_detail):
                    logger.info("clerk_org_member_already_exists", org_id=org_id, user_id=user_id)
                    return True
                logger.warning("clerk_add_member_validation", errors=error_detail)
                return False
            else:
                logger.error("clerk_add_member_error", status=response.status_code, body=response.text)
                return False
        except Exception as e:
            logger.error("clerk_add_member_exception", error=str(e))
            return False

    def get_user_organization_memberships(self, user_id: str) -> List[Dict[str, Any]]:
        """Gets all organization memberships for a Clerk user."""
        if not self.secret_key:
            return []

        url = f"{self.api_url}/users/{user_id}/organization_memberships"
        headers = {"Authorization": f"Bearer {self.secret_key}"}

        try:
            response = httpx.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", data) if isinstance(data, dict) else data
            return []
        except Exception as e:
            logger.error("clerk_get_memberships_error", error=str(e))
            return []

    def delete_user(self, user_id: str) -> bool:
        """
        Deletes the user.
        """
        if not self.secret_key:
            return False

        url = f"{self.api_url}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {self.secret_key}"
        }

        try:
            response = httpx.delete(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                logger.info("clerk_user_deleted", user_id=user_id)
                return True
            else:
                logger.error("clerk_user_delete_failed", status=response.status_code, body=response.text)
                return False
        except Exception as e:
            logger.error("clerk_user_delete_exception", error=str(e))
            return False
