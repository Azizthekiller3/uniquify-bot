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
    """Bind the HTTP health server and signal when ready."""
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        print(f"[health] Listening on port {port}", flush=True)
        _health_ready.set()          # unblock the main thread
        server.serve_forever()
    except OSError as exc:
        print(f"[health] Could not bind to port {port}: {exc}", flush=True)
        _health_ready.set()          # still unblock so main thread proceeds


# ── 1. Start health server in a daemon thread ─────────────────────────────────
# Daemon: it exits automatically when the main thread (bot) exits, so Render
# sees the process die and restarts the service on bot crash.
health_thread = threading.Thread(target=start_health_server, daemon=True)
health_thread.start()

# Wait until the port is actually bound (typically <10 ms).
# This guarantees Render's health probe sees an open port before we spend
# time on the bot's Telegram connection.
_health_ready.wait(timeout=5)

# ── 2. Run the bot in the MAIN thread ────────────────────────────────────────
# Pyrogram's Client.run() installs OS signal handlers (SIGINT/SIGTERM) via
# Python's signal module, which only works in the main thread.  Running the
# bot here keeps everything correct and lets the process exit cleanly on crash
# so Render auto-restarts the service.
from bot import Bot
Bot().run()
