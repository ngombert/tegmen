import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from common.auth import decode_token
from common.config import config

def test_decode_valid_token():
    payload = {"family_id": "fam-1", "sub": "user-1"}
    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    
    decoded = decode_token(token)
    assert decoded["family_id"] == "fam-1"
    assert decoded["sub"] == "user-1"

def test_decode_expired_token():
    payload = {
        "family_id": "fam-1", 
        "exp": datetime.now(timezone.utc) - timedelta(minutes=10)
    }
    token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)
    assert excinfo.value.status_code == 401
    assert "expiré" in excinfo.value.detail

def test_decode_invalid_token():
    token = "invalid.token.here"
    
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)
    assert excinfo.value.status_code == 401
    assert "invalide" in excinfo.value.detail

def test_decode_wrong_secret():
    payload = {"family_id": "fam-1"}
    token = jwt.encode(payload, "wrong-secret", algorithm=config.JWT_ALGORITHM)
    
    with pytest.raises(HTTPException) as excinfo:
        decode_token(token)
    assert excinfo.value.status_code == 401
