"""
Zero-Dependency Local Web Server for Kisan Mitra AI.
Provides full HTTP REST APIs and serves the responsive single-page web application.
Can be executed immediately via:
    python3 web_server.py
"""
import os
import sys
import signal
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import TCPServer

# Allow port reuse immediately upon restart
TCPServer.allow_reuse_address = True
from agent import FarmerAdvisoryAssistant
from evaluate import run_evaluation

# Global assistant instance
ASSISTANT = FarmerAdvisoryAssistant()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

class FarmerAdvisoryHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
            with open(file_path, "rb") as f:
                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(f.read())
            return
        elif path == "/style.css":
            file_path = os.path.join(STATIC_DIR, "style.css")
            with open(file_path, "rb") as f:
                self._set_headers(200, "text/css; charset=utf-8")
                self.wfile.write(f.read())
            return
        elif path == "/script.js":
            file_path = os.path.join(STATIC_DIR, "script.js")
            with open(file_path, "rb") as f:
                self._set_headers(200, "application/javascript; charset=utf-8")
                self.wfile.write(f.read())
            return
        elif path == "/api/tool/mandi":
            query_params = urllib.parse.parse_qs(parsed.query)
            crop = query_params.get("crop", ["wheat"])[0]
            msp = ASSISTANT.mandi_tool.get_msp(crop)
            rates = ASSISTANT.mandi_tool.get_mandi_rates(crop)
            res = {"msp_info": msp, "mandi_rates": rates}
            self._set_headers(200)
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        payload = json.loads(body) if body else {}

        if path == "/api/query":
            query = payload.get("query", "")
            lang = payload.get("language", "hin_Deva")
            acreage = float(payload.get("acreage", 1.0))
            result = ASSISTANT.process_query(query, user_language=lang, acreage=acreage)
            self._set_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/tool/fertilizer":
            crop = payload.get("crop", "wheat")
            acres = float(payload.get("acreage", 1.0))
            soil = payload.get("soil_status", "medium")
            result = ASSISTANT.fertilizer_tool.calculate(crop, acreage=acres, soil_health_status=soil)
            self._set_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/evaluate":
            eval_result = run_evaluation()
            self._set_headers(200)
            self.wfile.write(json.dumps(eval_result, ensure_ascii=False).encode("utf-8"))
            return

        self._set_headers(404, "text/plain")
        self.wfile.write(b"Not Found")

def run(port: int = 8080):
    server_address = ("", port)
    TCPServer.allow_reuse_address = True
    httpd = HTTPServer(server_address, FarmerAdvisoryHandler)

    def shutdown_handler(signum, frame):
        print("\n🌾 [Shutting down Kisan Mitra Web Server...]")
        try:
            httpd.server_close()
        except Exception:
            pass
        sys.exit(0)

    # Register OS-level signal traps for macOS/Linux
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    print("=" * 70)
    print(f"🌾 Kisan Mitra AI Web Server listening at: http://localhost:{port}")
    print("Zero external web dependencies required. Open in your browser!")
    print("Press Control+C (or Control+\\) to stop.")
    print("=" * 70)
    try:
        httpd.serve_forever(poll_interval=0.5)
    except (KeyboardInterrupt, SystemExit):
        print("\nServer shutting down gracefully.")
        try:
            httpd.server_close()
        except Exception:
            pass
        sys.exit(0)

if __name__ == "__main__":
    run()
