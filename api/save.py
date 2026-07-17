"""
Vercel serverless — 存整份 profile.json，commit 回 GitHub。
需帶正確密碼（比對環境變數 ADMIN_PASSWORD）。
"""

from http.server import BaseHTTPRequestHandler
import base64
import json
import os
import time
import urllib.request
import urllib.error

GITHUB_PAT     = os.environ.get("GITHUB_PAT", "")
GITHUB_OWNER   = os.environ.get("GITHUB_OWNER", "")
GITHUB_REPO    = os.environ.get("GITHUB_REPO", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
FILE_PATH      = "data/profile.json"

# 允許的頂層 key（白名單，避免寫入意料外的結構）
ALLOWED_KEYS = {
    "profile", "about", "interests", "links",
    "fandoms", "hobbies", "concerts", "support", "footer",
}


def _gh_get():
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{FILE_PATH}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
    })
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _gh_put(sha, content_obj):
    encoded = base64.b64encode(
        json.dumps(content_obj, ensure_ascii=False, indent=2).encode()
    ).decode()
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{FILE_PATH}"
    body = {"message": "chore: update profile via admin", "content": encoded}
    if sha:
        body["sha"] = sha
    payload = json.dumps(body).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, method="PUT")
    with urllib.request.urlopen(req) as r:
        return r.status in (200, 201)


class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
        except Exception:
            self._respond({"success": False, "error": "invalid JSON"}, 400)
            return

        if not ADMIN_PASSWORD or data.get("password") != ADMIN_PASSWORD:
            self._respond({"success": False, "error": "密碼錯誤"}, 401)
            return

        # 僅驗證密碼（後台登入用），不寫入
        if data.get("verify"):
            self._respond({"success": True})
            return

        profile = data.get("profile")
        if not isinstance(profile, dict):
            self._respond({"success": False, "error": "missing profile"}, 400)
            return

        # 只保留白名單 key
        clean = {k: v for k, v in profile.items() if k in ALLOWED_KEYS}
        if not clean:
            self._respond({"success": False, "error": "empty profile"}, 400)
            return

        for attempt in range(4):
            if attempt > 0:
                time.sleep(0.8)
            try:
                meta = _gh_get()
                sha = meta["sha"] if meta else None
                _gh_put(sha, clean)
                self._respond({"success": True})
                return
            except urllib.error.HTTPError as e:
                if e.code == 409 and attempt < 3:
                    continue
                self._respond({"success": False, "error": f"GitHub {e.code}"}, 502)
                return
            except Exception as e:
                self._respond({"success": False, "error": str(e)}, 500)
                return

        self._respond({"success": False, "error": "重試失敗"}, 502)

    def _respond(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
