import jwt
from datetime import datetime, timezone
from typing import Optional, Dict
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from common.config import config
from common.logger import setup_logger

logger = setup_logger("auth")

security = HTTPBearer(auto_error=False)

def decode_token(token: str) -> Dict:
    """
    Decode and validate a JWT token.
    Returns the decoded payload or raises HTTPException.
    """
    try:
        payload = jwt.decode(
            token, 
            config.JWT_SECRET, 
            algorithms=[config.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail="Jeton invalide")
    except Exception as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(status_code=401, detail="Erreur d'authentification")

async def get_current_identity(res: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Dependency to get the current authenticated identity from the Bearer token.
    Excludes PUBLIC routes if needed, but here it's mandatory unless specified.
    """
    if not res:
        raise HTTPException(status_code=401, detail="Authentification requise (Bearer token manquant)")
    
    return decode_token(res.credentials)
