import sys
from pathlib import Path
import unittest

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient

from src.main import app


API_KEY = "test_api_key_12345"


class TestGmailCategorizerAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        with open("ignore/message.txt", "r") as f:
            self.sample_email_text = f.read()

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_unauthorized_without_api_key(self):
        response = self.client.post("/parse", json={"message": self.sample_email_text})
        self.assertEqual(response.status_code, 401)

    def test_user_exact_curl_payload_without_content_type(self):
        # Simulates curl -d without -H "Content-Type: application/json"
        raw_payload = """{
    "message": "New form submission on Portfolio Funnel Form\\n\\nSomeone just submitted a form on portfolio-seven-iota-92.vercel.app/. Here\\x27s what they had to say:\\n\\nname\\n\\nketo\\nemail\\n\\ntest@gmail.com\\nmessage\\n\\nThis is a test message to check if the mail service is working or not."
  }"""
        response = self.client.post(
            "/parse",
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            content=raw_payload,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["client_name"], "keto")
        self.assertEqual(data["client_mail"], "test@gmail.com")
        self.assertEqual(
            data["message"],
            "This is a test message to check if the mail service is working or not.",
        )
        self.assertEqual(data["group"], "Portfolio Funnel Form")

    def test_parse_from_file_content(self):
        response = self.client.post(
            "/parse",
            headers={"X-API-Key": API_KEY, "Content-Type": "text/plain"},
            content=self.sample_email_text,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["client_name"], "keto")
        self.assertEqual(data["client_mail"], "test@gmail.com")
        self.assertEqual(
            data["message"],
            "This is a test message to check if the mail service is working or not.",
        )
        self.assertEqual(data["group"], "Portfolio Funnel Form")

    def test_parse_json_message(self):
        response = self.client.post(
            "/parse",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"message": self.sample_email_text},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["client_name"], "keto")
        self.assertEqual(data["client_mail"], "test@gmail.com")
        self.assertEqual(
            data["message"],
            "This is a test message to check if the mail service is working or not.",
        )

    def test_query_param_auth(self):
        response = self.client.post(
            f"/parse?apiKey={API_KEY}",
            json={"message": self.sample_email_text},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["client_name"], "keto")
        self.assertEqual(data["client_mail"], "test@gmail.com")


if __name__ == "__main__":
    unittest.main()
