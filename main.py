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


def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        server.serve_forever()
    except OSError as e:
        # Port already in use (e.g. local dev env) — health server skipped.
        # On Render, PORT is assigned dynamically and will always be free.
        print(f"[health] Could not bind to port {port}: {e} — skipping health server")


# Start the health server in a daemon thread so it exits automatically
# when the bot process stops. Render's free tier requires an open HTTP
# port to classify this as a web service (not a paid background worker).
# UptimeRobot then pings this endpoint every 5 minutes to keep it awake.
thread = threading.Thread(target=start_health_server, daemon=True)
thread.start()

Bot().run()
