import json
import re
from typing import Any, Dict, Optional


def parse_gmail_content(raw_input: str) -> Dict[str, str]:
    """
    Parses a Formspree / Gmail notification message and extracts:
      - group (form name / funnel form)
      - client_name
      - client_mail
      - message (clean form message content)
    Handles:
      - Raw text email body
      - JSON string (e.g., when sent without application/json header)
      - Escaped newlines (\\n, \\r\\n) and character escapes
    """
    if not raw_input or not raw_input.strip():
        return {
            "group": "Portfolio Funnel Form",
            "client_name": "",
            "client_mail": "",
            "message": "",
        }

    text = raw_input.strip()
    group_override = None
    client_name_override = None
    client_mail_override = None
    explicit_message = None

    # Step 1: Detect if text is wrapped in JSON (e.g. from curl or webhook without Content-Type header)
    if (text.startswith("{") and text.endswith("}")) or (text.startswith('{\n') or text.startswith('{\r\n')):
        try:
            data = json.loads(text, strict=False)
            if isinstance(data, dict):
                group_override = data.get("group")
                client_name_override = data.get("client_name")
                client_mail_override = data.get("client_mail")
                # If both client_name and client_mail were directly supplied, the message field might already be the clean message
                inner_msg = (
                    data.get("message")
                    or data.get("raw_message")
                    or data.get("email_body")
                    or data.get("content")
                    or data.get("text")
                )
                if inner_msg:
                    text = str(inner_msg)
                if client_name_override and client_mail_override and data.get("message"):
                    explicit_message = data.get("message")
        except Exception:
            # Fallback regex extraction of "message" field if JSON decode fails
            m = re.search(r'"message"\s*:\s*"(.*?)"(?:\s*})?$', text, re.DOTALL)
            if m:
                text = m.group(1)

    # Step 2: Normalize string (handle literal escapes like \n, \r, \x27, \')
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\\n" in text:
        text = text.replace("\\n", "\n")
    if "\\x27" in text:
        text = text.replace("\\x27", "'")
    if "\\'" in text:
        text = text.replace("\\'", "'")
    if '\\"' in text:
        text = text.replace('\\"', '"')

    # Step 3: Extract Group / Form Name
    # Formspree standard: "New form submission on <Form Name>"
    group = group_override
    if not group:
        group_m = re.search(r"New form submission on\s+([^\r\n]+)", text, re.IGNORECASE)
        if group_m:
            group = group_m.group(1).strip()
        else:
            domain_m = re.search(r"submitted a form on\s+([^\s/]+)", text, re.IGNORECASE)
            if domain_m:
                group = domain_m.group(1).strip()
            else:
                group = "Portfolio Funnel Form"

    # Step 4: Extract Client Name
    # In Formspree:
    # name
    # keto
    client_name = client_name_override
    if not client_name:
        name_m = re.search(
            r"(?:^|\n)\s*(?:name|client[\s_]*name|full[\s_]*name)\s*[:\n\-]+\s*([^\r\n]+)",
            text,
            re.IGNORECASE,
        )
        if name_m:
            client_name = name_m.group(1).strip()
        else:
            client_name = ""

    # Step 5: Extract Client Email
    # In Formspree:
    # email
    # test@gmail.com
    client_mail = client_mail_override
    if not client_mail:
        mail_m = re.search(
            r"(?:^|\n)\s*(?:email|client[\s_]*mail|mail)\s*[:\n\-]+\s*([^\r\n]+)",
            text,
            re.IGNORECASE,
        )
        if mail_m:
            # Extract pure email from that line
            line = mail_m.group(1).strip()
            sub_m = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", line)
            client_mail = sub_m.group(1).strip() if sub_m else line
        else:
            # Fallback to email regex ensuring word boundary/no preceding alphanumeric/backslash
            sub_m = re.search(r"(?<![a-zA-Z0-9_\\/])([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
            client_mail = sub_m.group(1).strip() if sub_m else ""

    # Step 6: Extract Message Content
    if explicit_message:
        final_message = explicit_message
    else:
        # In Formspree:
        # message
        # This is a test message to check if the mail service is working or not.
        msg_m = re.search(
            r"(?:^|\n)\s*(?:message|client[\s_]*message|comments?|body)\s*[:\n\-]+\s*(.+)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if msg_m:
            final_message = msg_m.group(1).strip()
        else:
            final_message = text.strip()

    return {
        "group": group,
        "client_name": client_name,
        "client_mail": client_mail,
        "message": final_message,
    }
