import base64
import hashlib

from cryptography.fernet import Fernet
from passlib.context import CryptContext

from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_key() -> bytes:
    """Generate a random key for encryption."""
    return Fernet.generate_key()


def encrypt_string(text: str, key: str) -> str:
    """Encrypt a string using Fernet (symmetric encryption)."""
    f = Fernet(key.encode())
    return f.encrypt(text.encode()).decode()


def decrypt_string(token: str, key: str) -> str:
    """Decrypt a string using Fernet."""
    f = Fernet(key.encode())
    return f.decrypt(token.encode()).decode()


def get_encryption_key() -> str:
    """Derives a URL-safe base64 32-byte key from settings.API_SECRET_KEY."""
    digest = hashlib.sha256(settings.API_SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode()
