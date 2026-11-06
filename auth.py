import os
import secrets
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

load_dotenv()

API_KEY_ENV = os.getenv("API_KEY")

if not API_KEY_ENV:
    raise ValueError("API_KEY environment variable is not set")

_EXPECTED_KEY = API_KEY_ENV.encode("utf-8")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="apiKey", auto_error=False)


async def verify_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
) -> None:
    """
    Validates the API key from the X-API-Key header or the apiKey query parameter.
    Raises HTTP 401 if the key is missing or invalid.
    """
    provided_key = header_key or query_key

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide it via the X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not secrets.compare_digest(provided_key.encode("utf-8"), _EXPECTED_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )