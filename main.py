import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from bot import Bot


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        # Suppress noisy access logs from the health pings
        pass


def run_bot():
    """Run the bot in a background thread with its own asyncio event loop."""
    try:
        Bot().run()
    except Exception as exc:
        import logging
        logging.error(f"[bot] crashed: {exc}", exc_info=True)
        # Don't kill the process — keep the health server alive so Render
        # doesn't mark the service as down.


# Start the bot in a daemon thread (exits automatically when the process stops).
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

# Run the HTTP health server in the MAIN thread so the process stays alive
# even if the bot crashes.  Render's free web service requires an open HTTP
# port; UptimeRobot pings it every 5 minutes to prevent the service sleeping.
port = int(os.environ.get("PORT", 8080))
try:
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"[health] Listening on port {port}")
    server.serve_forever()
except OSError as exc:
    print(f"[health] Could not bind to port {port}: {exc} — waiting for bot thread")
    bot_thread.join()  # Fall back: keep process alive until bot exits naturally
