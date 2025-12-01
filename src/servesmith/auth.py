"""API key authentication middleware."""

import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Default dev key, override via SERVESMITH_API_KEY env var
_API_KEY = os.environ.get("SERVESMITH_API_KEY", "dev123")


def require_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> str:
    """Validate API key from request header."""
    if not api_key or api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
