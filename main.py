import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
import uvicorn

from auth import verify_api_key
from parser import parse_gmail_content
from type import EmailParseResponse, InputMessageMeta, OutputMessageMeta



load_dotenv()

app = FastAPI(
    title="Telegram Categorizer - Gmail / Formspree Parsing API",
    description="FastAPI service to parse Formspree and Gmail notification emails for Make / workflow automation.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "telegram-categorizer-mail-parser"}


@app.post(
    "/parse",
    response_model=EmailParseResponse,
    tags=["Parser"],
    summary="Parse incoming Formspree / Gmail notification",
    dependencies=[Depends(verify_api_key)],
)
@app.post(
    "/message",
    response_model=EmailParseResponse,
    include_in_schema=False,
    dependencies=[Depends(verify_api_key)],
)
@app.post(
    "/",
    response_model=EmailParseResponse,
    include_in_schema=False,
    dependencies=[Depends(verify_api_key)],
)
async def parse_message_endpoint(
    request: Request,
    api_key: str = Depends(verify_api_key),
) -> EmailParseResponse:
    # Read the full raw body first
    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8", errors="replace").strip()

    if not body_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Request body is empty.",
        )

    platform = "gmail"
    group_override = None
    client_name = None
    client_mail = None
    raw_text = None
    explicit_message = None

    # Step 1: Detect if body is JSON (even if Content-Type was omitted in curl/webhook)
    body_json = None
    if (body_text.startswith("{") and body_text.endswith("}")) or "application/json" in request.headers.get("content-type", "").lower():
        try:
            body_json = json.loads(body_text, strict=False)
        except Exception:
            try:
                body_json = await request.json()
            except Exception:
                pass

    if isinstance(body_json, dict):
        platform = body_json.get("platform", "gmail")
        group_override = body_json.get("group")
        client_name = body_json.get("client_name")
        client_mail = body_json.get("client_mail")
        raw_text = (
            body_json.get("raw_message")
            or body_json.get("email_body")
            or body_json.get("content")
            or body_json.get("text")
            or body_json.get("message")
        )
        if client_name and client_mail and body_json.get("message"):
            explicit_message = body_json["message"]
    else:
        # Raw plain text body
        raw_text = body_text

    # Step 2: Parse content using Formspree / Gmail parser
    parsed = parse_gmail_content(raw_text or "")

    # Step 3: Resolve final field values
    final_client_name = client_name if client_name is not None else parsed["client_name"]
    final_client_mail = client_mail if client_mail is not None else parsed["client_mail"]
    final_group = group_override if group_override is not None else parsed["group"]
    final_message = explicit_message if explicit_message is not None else parsed["message"]

    now = datetime.now(timezone.utc)

    output_meta = OutputMessageMeta(
        platform=platform,
        client_name=final_client_name,
        client_mail=final_client_mail,
        message=final_message,
        timestamp=now,
        group=final_group,
    )

    return EmailParseResponse(
        platform=output_meta.platform,
        client_name=output_meta.client_name,
        client_mail=output_meta.client_mail,
        message=output_meta.message,
        timestamp=output_meta.timestamp,
        group=output_meta.group,
    )


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
