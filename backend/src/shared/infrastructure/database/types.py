"""Custom SQLAlchemy column types for encrypted storage."""

import json
from typing import Any

from sqlalchemy import Dialect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

from src.core.security import decrypt_string, encrypt_string, get_encryption_key


class EncryptedJSON(TypeDecorator):
    """Encrypt JSON on write, decrypt on read, with legacy plaintext fallback.

    Handles both legacy plaintext JSON and new encrypted JSON wrapped
    in ``{"_encrypted": "..."}``.
    """

    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: dict | list | None, dialect: Dialect) -> dict | None:
        """Encrypt and wrap JSON value before database insert."""
        if value is None:
            return None

        # Serialize the JSON object to a string
        json_str = json.dumps(value)

        # Encrypt the string
        key = get_encryption_key()
        encrypted_str = encrypt_string(json_str, key)

        # Return as a JSON object with a specific key to mark it as encrypted
        return {"_encrypted": encrypted_str}

    def process_result_value(self, value: Any | None, dialect: Dialect) -> dict | list | None:  # noqa: ANN401 — generic SA type handler
        """Decrypt value on read, passing through legacy plaintext."""
        if value is None:
            return None

        # Check if the value is a dict and has the encryption marker
        if isinstance(value, dict) and "_encrypted" in value:
            encrypted_str = value["_encrypted"]
            key = get_encryption_key()
            decrypted_json_str = decrypt_string(encrypted_str, key)
            return json.loads(decrypted_json_str)

        # If it's not encrypted (legacy data), return as is
        return value
