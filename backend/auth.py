import os
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet

# Secret keys (load from env in prod)
SECRET_KEY = os.environ.get("JWT_SECRET", "supersecretkey_change_me_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Encryption for API Keys ---

def _get_fernet() -> Fernet:
    """Generate a valid 32 URL-safe base64-encoded Fernet key from the JWT_SECRET."""
    hasher = hashlib.sha256()
    hasher.update(SECRET_KEY.encode('utf-8'))
    # Fernet requires a 32-byte url-safe base64 encoded string
    key = base64.urlsafe_b64encode(hasher.digest())
    return Fernet(key)

_fernet = _get_fernet()

def encrypt_api_key(api_key: str) -> str:
    """Encrypt a plain text API key."""
    if not api_key:
        return ""
    return _fernet.encrypt(api_key.encode('utf-8')).decode('utf-8')

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an encrypted API key."""
    if not encrypted_key:
        return ""
    try:
        return _fernet.decrypt(encrypted_key.encode('utf-8')).decode('utf-8')
    except Exception:
        return ""
