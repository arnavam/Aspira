import pytest
from datetime import timedelta
from jose import jwt
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    encrypt_api_key,
    decrypt_api_key,
    SECRET_KEY,
    ALGORITHM
)


def test_password_hashing():
    password = "super_secure_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False
    assert verify_password(password, "invalid_hash_string") is False


def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data=data, expires_delta=timedelta(minutes=30))
    
    # Verify token can be decoded
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == "testuser"
    assert "exp" in payload


def test_api_key_encryption():
    api_key = "gsk_1234567890abcdefghijklmnopqrstuvwxyz"
    
    encrypted = encrypt_api_key(api_key)
    assert encrypted != api_key
    assert len(encrypted) > 0
    
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == api_key


def test_api_key_encryption_empty():
    assert encrypt_api_key("") == ""
    assert decrypt_api_key("") == ""
    assert decrypt_api_key("invalid_encrypted_string") == ""
