from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.constants import ALGORITHMS
import requests
import json
import os
from typing import Dict, Any, Optional
from functools import wraps

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization code.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication scheme.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        try:
            # Get Supabase JWT public key
            jwks_url = f"{os.getenv('SUPABASE_URL')}/auth/v1/.well-known/jwks.json"
            jwks = requests.get(jwks_url).json()

            # Get the key ID from the token header
            header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break

            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find appropriate key",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Verify the token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=[ALGORITHMS.RS256],
                audience="authenticated",
                issuer=os.getenv('SUPABASE_URL') + "/auth/v1"
            )

            # Add user info to request state
            request.state.user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role")
            }

            return request.state.user

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token or expired token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

def get_current_user(request: Request) -> Dict[str, Any]:
    """Dependency to get the current user from the request"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return request.state.user
