import os
import secrets
from typing import Optional
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

load_dotenv()

API_KEY_ENV = os.getenv("API_KEY", "default_secret_key_12345")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="apiKey", auto_error=False)


async def verify_api_key(
    request: Request,
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
) -> str:
    """
    Validates API key provided via header, query parameter, or Authorization header.
    Returns the valid API key or raises HTTP 401.
    """
    provided_key: Optional[str] = None

    if header_key:
        provided_key = header_key
    elif query_key:
        provided_key = query_key
    else:
        alt_headers = ["apikey"]
        for h in alt_headers:
            if h in request.headers:
                provided_key = request.headers[h]
                break

        if not provided_key and "authorization" in request.headers:
            auth_val = request.headers["authorization"].strip()

            parts = auth_val.split(maxsplit=1)
            if len(parts) == 2 and parts[0].lower() in ["bearer", "apikey", "key"]:
                provided_key = parts[1]
            elif len(parts) == 1:
                provided_key = parts[0]

    if not provided_key or not secrets.compare_digest(provided_key, API_KEY_ENV):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Provide it via X-API-Key header or ?apiKey= query param.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return provided_key

