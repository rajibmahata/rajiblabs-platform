""" 
RajibLabs Subscriber Webhook
Minimal Python HTTP server that accepts email subscriptions
and sends Telegram notifications to Rajib.
"""
import json
import os
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

PORT = 5099
SUBSCRIBERS_FILE = os.path.join(os.path.dirname(__file__), "subscribers.json")
# Telegram Bot Token and Chat ID from OpenClaw config
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = "5090593178"

def send_telegram(text: str):
    """Send a Telegram message to Rajib."""
    if not TELEGRAM_BOT_TOKEN:
        print("[webhook] No TELEGRAM_BOT_TOKEN set — skipping Telegram notification")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"[webhook] Telegram send failed: {e}")
        return False

def save_subscriber(email: str) -> list:
    """Save subscriber email to JSON file, return updated list."""
    subscribers = []
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE) as f:
                subscribers = json.load(f)
        except (json.JSONDecodeError, IOError):
            subscribers = []
    
    # Avoid duplicates
    for sub in subscribers:
        if sub.get("email") == email:
            return subscribers
    
    subscribers.append({
        "email": email,
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
    })
    
    os.makedirs(os.path.dirname(SUBSCRIBERS_FILE) or ".", exist_ok=True)
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f, indent=2)
    
    return subscribers

class SubscriberHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/subscribe":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            email = data.get("email", "").strip()
        except (json.JSONDecodeError, ValueError):
            self._error("Invalid JSON")
            return

        if not email or "@" not in email:
            self._error("Valid email required")
            return

        # Save subscriber
        subscribers = save_subscriber(email)
        count = len(subscribers)

        # Notify via Telegram
        msg = (
            f"🆕 <b>New Subscriber</b>\n\n"
            f"📧 {email}\n"
            f"📊 Total subscribers: {count}\n"
            f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        )
        send_telegram(msg)

        # Success
        self.send_response(200)
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "message": "Subscribed!"}).encode())

    def _error(self, message: str):
        self.send_response(400)
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"status": "error", "message": message}).encode())

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")

    def log_message(self, format, *args):
        print(f"[webhook] {args[0]}")

if __name__ == "__main__":
    print(f"[webhook] Starting subscriber service on port {PORT}...")
    server = HTTPServer(("0.0.0.0", PORT), SubscriberHandler)
    print(f"[webhook] Listening on http://0.0.0.0:{PORT}/api/subscribe")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[webhook] Shutting down...")
        server.server_close()
