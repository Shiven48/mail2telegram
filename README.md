# Telegram Categorizer - Gmail Parsing Service

A lightweight, high-performance FastAPI service designed to ingest and parse incoming Gmail / Web form submissions (such as portfolio contact forms) for workflow automation tools like Make.com, n8n, and Zapier.

## Features

- **Automated Email Parsing**: Extracts `client_name`, `client_mail` and clean `message` from raw notification emails.
- **API Key Authentication**: Secure endpoint protected via `apiKey` (supports `X-API-Key` header, `apiKey` query parameter, or `Authorization: Bearer <key>`).
- **Flexible Ingestion**: Accepts JSON payloads (such as `InputMessageMeta` or `{ "message": "..." }`) and raw plain-text email bodies.
- **Dependency Management with `uv`**: Ultra-fast environment and package management.
- **Standardized Output**: Returns `OutputMessageMeta` with timestamps in UTC.

---

## Data Models

### Input Structure (`InputMessageMeta`)

```python
@dataclass
class InputMessageMeta:
    platform: str = "gmail"        # Source platform (e.g., gmail)
    client_name: Optional[str]     # e.g., Keto
    client_mail: Optional[str]     # e.g., test@gmail.com
    message: Optional[str]         # Raw email or inner message
```

### Output Structure (`OutputMessageMeta`)

```python
@dataclass
class OutputMessageMeta:
    platform: str                  # e.g., gmail
    client_name: str               # e.g., keto
    client_mail: str               # e.g., test@gmail.com
    message: str                   # Clean message body
    timestamp: datetime            # Timestamp of parsing
```

---

## Installation & Setup

### 1. Requirements

- Python >= 3.10
- [`uv`](https://docs.astral.sh/uv/) package manager

### 2. Environment Configuration

Copy `.env.example` to `.env` and set your secret API key:

```bash
cp .env.example .env
```

Example `.env`:

```env
API_KEY=test_api_key_12345
HOST=0.0.0.0
PORT=8000
```

### 3. Install Dependencies

Using `uv`:

```bash
uv sync
```

---

## Running the Server

Start the FastAPI application:

```bash
uv run python main.py
```

Or directly using `uvicorn`:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Usage & API Reference

### Endpoint: `POST /parse`

Authentication: Header `X-API-Key: <your_api_key>` or query parameter `?apiKey=<your_api_key>`

#### Example 1: Sending Raw Email Text in JSON (Common in Make / Zapier)

```bash
curl -X POST http://localhost:8000/parse \
  -H "X-API-Key: test_api_key_12345" \
  -H "Content-Type: application/text" \
  -d '{
    "message": "New form submission on Portfolio Funnel Form\n\nSomeone just submitted a form on portfolio-seven-iota-92.vercel.app/. Here\x27s what they had to say:\n\nname\n\nketo\nemail\n\ntest@gmail.com\nmessage\n\nThis is a test message to check if the mail service is working or not."
  }'
```

#### Example 2: Sending Pre-Structured JSON

```bash
curl -X POST http://localhost:8000/parse \
  -H "X-API-Key: test_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "gmail",
    "client_name": "Keto",
    "client_mail": "test@gmail.com",
    "message": "This is a test message to check if the mail service is working or not."
  }'
```

#### Example 3: Sending Plain Text Body

```bash
curl -X POST "http://localhost:8000/parse?apiKey=test_api_key_12345" \
  -H "Content-Type: text/plain" \
  --data-binary @ignore/message.txt
```

#### Response (HTTP 200 OK)

```json
{
  "platform": "gmail",
  "client_name": "keto",
  "client_mail": "test@gmail.com",
  "message": "This is a test message to check if the mail service is working or not.",
  "timestamp": "2026-11-06T01:15:30.123456Z"
}
```

---

<!-- ## Make.com Workflow Setup Guide

1. **Trigger Module**: **Gmail -> Watch Emails**
   - Filter emails by sender, subject, or label (e.g. `Subject contains "New form submission"`).
2. **Action Module**: **HTTP -> Make a request**
   - **URL**: `https://<your-deployed-domain>/parse`
   - **Method**: `POST`
   - **Headers**:
     - `Content-Type`: `application/json`
     - `X-API-Key`: `<your_api_key>`
   - **Body type**: `Raw`
   - **Content type**: `JSON (application/json)`
   - **Request content**:
     ```json
     {
       "message": "{{1.text}}"
     }
     ```
   - **Parse response**: `Yes`
3. **Next Module**: Telegram / CRM / Database
   - Access parsed fields:
     - `{{2.data.client_name}}`
     - `{{2.data.client_mail}}`
     - `{{2.data.message}}`
     - `{{2.data.timestamp}}` -->
