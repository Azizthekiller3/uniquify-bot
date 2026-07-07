import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # silence access logs


_health_ready = threading.Event()


def start_health_server():
    """Bind the HTTP health server and signal when the port is open."""
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        print(f"[health] Listening on port {port}", flush=True)
        _health_ready.set()      # tell main thread the port is bound
        server.serve_forever()
    except OSError as exc:
        print(f"[health] Bind failed on port {port}: {exc}", flush=True)
        _health_ready.set()      # unblock main thread even on failure


# ── 1. Start health server in a daemon thread ─────────────────────────────────
# daemon=True: the health server exits automatically when the bot (main thread)
# exits, so Render sees the process die and restarts the service.
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

# Wait until the port is actually bound before starting the bot (typically <10 ms).
# Render's health probe then sees an open port immediately.
_health_ready.wait(timeout=5)

# ── 2. Run the bot in the MAIN thread ────────────────────────────────────────
# Pyrogram's Client.run() installs OS signal handlers (SIGINT/SIGTERM) which
# Python's signal module only permits in the main thread.
# Requires Python ≤ 3.11: Pyrogram 2.0.x calls asyncio.get_event_loop() at
# import time (sync.py), which Python 3.12+ no longer supports automatically.
# The .python-version file pins Render to Python 3.11.
from bot import Bot
Bot().run()
