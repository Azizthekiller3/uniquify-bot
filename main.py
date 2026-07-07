import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Shared bot state so the health endpoint can report it.
_bot_status = "starting"   # starting | running | crashed | stopped
_bot_error  = ""


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        code = 200 if _bot_status in ("starting", "running") else 503
        self.send_response(code)
        self.end_headers()
        body = f"status={_bot_status}"
        if _bot_error:
            body += f" | {_bot_error[:200]}"
        self.wfile.write(body.encode())

    def log_message(self, format, *args):
        pass  # silence access logs


def run_bot():
    global _bot_status, _bot_error
    import logging

    # Python 3.10+ does not create an event loop automatically in non-main
    # threads.  Pyrogram's Client.run() calls asyncio.get_event_loop() which
    # raises "There is no current event loop" without this.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        from bot import Bot
        _bot_status = "running"
        Bot().run()
        _bot_status = "stopped"
    except Exception as exc:
        _bot_error  = str(exc)
        _bot_status = "crashed"
        logging.error("[bot] crashed: %s", exc, exc_info=True)
    finally:
        loop.close()


# ── 1. Bind the health server FIRST, before any bot imports ──────────────────
port = int(os.environ.get("PORT", 8080))
try:
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"[health] Listening on port {port}", flush=True)
except OSError as exc:
    print(f"[health] Could not bind to port {port}: {exc}", flush=True)
    server = None

# ── 2. Start the bot in a daemon thread ──────────────────────────────────────
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

# ── 3. Serve health checks on the main thread (keeps process alive) ───────────
if server:
    server.serve_forever()
else:
    bot_thread.join()
