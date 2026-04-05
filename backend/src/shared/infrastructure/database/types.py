import json
from typing import Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

from src.core.security import decrypt_string, encrypt_string, get_encryption_key


class EncryptedJSON(TypeDecorator):
    """
    SQLAlchemy TypeDecorator that encrypts JSON data before saving to the database
    and decrypts it when loading.

    It handles both legacy plaintext JSON and new encrypted JSON wrapped in {"_encrypted": "..."}.
    """

    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: dict | list | None, dialect) -> dict | None:
        if value is None:
            return None

        # Serialize the JSON object to a string
        json_str = json.dumps(value)

        # Encrypt the string
        key = get_encryption_key()
        encrypted_str = encrypt_string(json_str, key)

        # Return as a JSON object with a specific key to mark it as encrypted
        return {"_encrypted": encrypted_str}

    def process_result_value(self, value: Any | None, dialect) -> dict | list | None:
        if value is None:
            return None

        # Check if the value is a dict and has the encryption marker
        if isinstance(value, dict) and "_encrypted" in value:
            encrypted_str = value["_encrypted"]
            key = get_encryption_key()
            try:
                decrypted_json_str = decrypt_string(encrypted_str, key)
                return json.loads(decrypted_json_str)
            except Exception:
                # In case of decryption failure, we might want to log it or raise an error.
                # For now, let's re-raise to be safe.
                raise

        # If it's not encrypted (legacy data), return as is
        return value
