import os
import sys
import time
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

_bot_status = "starting"
_bot_error  = ""


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = 200 if _bot_status in ("starting", "running") else 503
        self.send_response(code)
        self.end_headers()
        body = f"status={_bot_status}"
        if _bot_error:
            body += f"\n{_bot_error}"
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        print(f"[health] Listening on port {port}", flush=True)
        server.serve_forever()
    except OSError as exc:
        print(f"[health] Bind failed: {exc}", flush=True)


# NON-daemon so the process keeps running even after the main-thread bot exits.
# This lets us read crash details via the health endpoint.
health_thread = threading.Thread(target=start_health_server, daemon=False)
health_thread.start()
time.sleep(0.5)  # give the server a moment to bind

import logging
try:
    from bot import Bot
    _bot_status = "running"
    Bot().run()
    _bot_status = "stopped"
except Exception:
    _bot_status = "crashed"
    _bot_error  = traceback.format_exc()
    logging.error("[bot] crashed:\n%s", _bot_error)
