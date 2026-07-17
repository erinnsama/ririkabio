"""
Vercel serverless — 上傳圖片，commit 進 assets/，回傳可用路徑。
需帶正確密碼（比對環境變數 ADMIN_PASSWORD）。
用時間戳命名避免瀏覽器/CDN 快取到舊圖。
"""

from http.server import BaseHTTPRequestHandler
import base64
import json
import os
import re
import time
import urllib.request
import urllib.error

GITHUB_PAT     = os.environ.get("GITHUB_PAT", "")
GITHUB_OWNER   = os.environ.get("GITHUB_OWNER", "")
GITHUB_REPO    = os.environ.get("GITHUB_REPO", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

EXT_OK = {"jpg", "jpeg", "png", "gif", "webp"}
MAX_BYTES = 4_000_000  # ~4MB，留餘裕給 Vercel body 限制


def _gh_put_binary(path, raw_bytes):
    encoded = base64.b64encode(raw_bytes).decode()
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    body = {"message": f"chore: upload {path} via admin", "content": encoded}
    payload = json.dumps(body).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, method="PUT")
    with urllib.request.urlopen(req) as r:
        return r.status in (200, 201)


def _slug(name):
    base = os.path.splitext(os.path.basename(name or "img"))[0]
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", base).strip("-").lower() or "img"
    return base[:40]


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

        data_url = data.get("dataUrl", "")
        filename = data.get("filename", "img")

        m = re.match(r"^data:image/([a-zA-Z0-9.+-]+);base64,(.+)$", data_url, re.S)
        if not m:
            self._respond({"success": False, "error": "圖片格式錯誤"}, 400)
            return

        ext = m.group(1).lower()
        if ext == "jpeg":
            ext = "jpg"
        if ext not in EXT_OK:
            self._respond({"success": False, "error": f"不支援的格式 {ext}"}, 400)
            return

        try:
            raw = base64.b64decode(m.group(2))
        except Exception:
            self._respond({"success": False, "error": "base64 解碼失敗"}, 400)
            return

        if len(raw) > MAX_BYTES:
            self._respond({"success": False, "error": "圖片過大（上限約 4MB）"}, 413)
            return

        path = f"assets/{_slug(filename)}-{int(time.time())}.{ext}"
        try:
            _gh_put_binary(path, raw)
            self._respond({"success": True, "path": path})
        except urllib.error.HTTPError as e:
            self._respond({"success": False, "error": f"GitHub {e.code}"}, 502)
        except Exception as e:
            self._respond({"success": False, "error": str(e)}, 500)

    def _respond(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass
