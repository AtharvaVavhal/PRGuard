#!/usr/bin/env python3
"""
Local integration test — simulates a GitHub webhook + mocks GitHub API calls.
Run with: USE_MOCK_AI=true python test_local.py

Does NOT require a real GitHub token or OpenAI key.
"""
import hashlib
import hmac
import json
import os
import unittest.mock as mock

# Force mock mode before importing app
os.environ["USE_MOCK_AI"] = "true"
os.environ["GITHUB_TOKEN"] = "fake-token"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"
os.environ["OPENAI_API_KEY"] = "fake-key"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FAKE_DIFF = """\
diff --git a/src/handler.py b/src/handler.py
index a1b2c3..d4e5f6 100644
--- a/src/handler.py
+++ b/src/handler.py
@@ -1,5 +1,45 @@
+import requests
+
+def process(d, db):
+    # validate
+    if d is None:
+        return None
+    if "id" not in d:
+        return None
+    if not isinstance(d["id"], int):
+        return None
+    if d["id"] < 0:
+        return None
+    # process
+    res = db.query("SELECT * FROM users WHERE id=" + str(d["id"]))
+    if res:
+        tmp = res[0]
+        payload = {"uid": tmp["id"], "n": tmp["name"]}
+        requests.post("https://api.example.com/notify", json=payload)
+        return payload
+    return None
"""

PAYLOAD = {
    "action": "opened",
    "pull_request": {
        "number": 42,
        "title": "Add user notification on login",
        "head": {"sha": "abc123def456"},
    },
    "repository": {"full_name": "testorg/testrepo"},
}


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    print("✅ Health check:", resp.json())


def test_webhook_ignored_event():
    resp = client.post(
        "/webhook/github",
        content=b"{}",
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": _sign(b"{}", "test-secret")},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"
    print("✅ Non-PR event correctly ignored")


def test_full_review():
    body = json.dumps(PAYLOAD).encode()
    sig = _sign(body, "test-secret")

    # Mock GitHub API calls so we don't need a real token
    with (
        mock.patch("app.github_client.get_pr_diff", return_value=FAKE_DIFF),
        mock.patch("app.github_client.set_commit_status") as mock_status,
        mock.patch("app.github_client.post_pr_comment") as mock_comment,
    ):
        resp = client.post(
            "/webhook/github",
            content=body,
            headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": sig},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

        # TestClient runs background tasks synchronously
        print("✅ Webhook accepted")
        print(f"   set_commit_status called {mock_status.call_count}x")
        print(f"   post_pr_comment called {mock_comment.call_count}x")

        if mock_comment.call_count > 0:
            comment_body = mock_comment.call_args[0][2]
            print("\n--- Generated PR Comment Preview ---")
            print(comment_body[:1000])
            print("---")


def test_bad_signature():
    body = json.dumps(PAYLOAD).encode()
    resp = client.post(
        "/webhook/github",
        content=body,
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": "sha256=badsig"},
    )
    assert resp.status_code == 401
    print("✅ Bad signature correctly rejected")


if __name__ == "__main__":
    print("\n=== PR Reviewer Local Tests ===\n")
    test_health()
    test_webhook_ignored_event()
    test_bad_signature()
    test_full_review()
    print("\n✅ All tests passed\n")
