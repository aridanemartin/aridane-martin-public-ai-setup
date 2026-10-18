#!/usr/bin/env python3
"""
compact-conversation's capture server.

One-shot, stdlib-only local HTTP server: the picker page POSTs its submission
here instead of copying to the clipboard, so the skill can pick it up without
asking the user to paste anything back. It does NOT build the artifact or spawn
anything itself — it only has what the page has (short previews), not the full
live conversation, so that part stays with the agent. See the
compact-conversation skill's Step 2/3 for how this fits into the workflow.

Usage: python3 server.py <port> <result_json_path> [idle_timeout_seconds]

Writes <result_json_path> with the POSTed payload once a submission arrives,
then exits. Exits with no file written if idle_timeout_seconds elapses first
(default 540s, under the calling Bash tool's 600s cap) or on SIGINT/SIGTERM.
"""
import json
import signal
import socketserver
import sys
import threading
from http.server import BaseHTTPRequestHandler

PORT = int(sys.argv[1])
RESULT_PATH = sys.argv[2]
IDLE_TIMEOUT = float(sys.argv[3]) if len(sys.argv) > 3 else 540.0


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/submit":
            self.send_response(404)
            self._cors()
            self.end_headers()
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception as exc:  # malformed body — tell the page, keep listening
            self.send_response(400)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode())
            return

        with open(RESULT_PATH, "w") as f:
            json.dump(payload, f, indent=2)

        body = json.dumps({"message": "Received — your agent will take it from here."}).encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, *args):
        pass  # quiet — the skill reports outcomes in chat, not on this console


def main():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)

    timer = threading.Timer(IDLE_TIMEOUT, httpd.shutdown)
    timer.daemon = True
    timer.start()

    def stop(_sig, _frame):
        httpd.shutdown()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    httpd.serve_forever()
    timer.cancel()


if __name__ == "__main__":
    main()
