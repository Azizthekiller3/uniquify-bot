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


def run_bot():
    """Import and run the bot inside a daemon thread.

    Importing here (not at module top-level) isolates any import error so
    it can't prevent the HTTP server from binding its port first.

    If the bot crashes for any reason (bad env, auth failure, runtime error),
    the process exits with code 1.  Render automatically restarts web services
    when the process exits, so this is the correct liveness behaviour — a
    silent zombie that keeps returning 200 while the bot is dead would be
    worse.
    """
    import logging
    try:
        from bot import Bot
        Bot().run()
    except Exception as exc:
        logging.error("[bot] crashed: %s", exc, exc_info=True)
    finally:
        # Terminate the whole process so Render restarts the container.
        logging.error("[bot] shutting down process — Render will restart.")
        os._exit(1)


# ── 1. Bind the health server FIRST (before any bot imports) ──────────────────
port = int(os.environ.get("PORT", 8080))
try:
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"[health] Listening on port {port}", flush=True)
except OSError as exc:
    print(f"[health] Could not bind to port {port}: {exc}", flush=True)
    server = None

# ── 2. Start bot in a daemon thread ───────────────────────────────────────────
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

# ── 3. Serve health checks on the main thread (keeps process alive) ───────────
if server:
    server.serve_forever()
else:
    bot_thread.join()
