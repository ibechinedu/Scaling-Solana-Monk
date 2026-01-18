#!/usr/bin/env python3
import os
import sys
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "solana-trading-bot"}')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    port = int(os.getenv('PORT', 9090))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Check if this is being called as a health check
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        try:
            response = requests.get('http://localhost:9090/health', timeout=5)
            if response.status_code == 200:
                sys.exit(0)
            else:
                sys.exit(1)
        except:
            sys.exit(1)
    else:
        # Start health server in background
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        time.sleep(1)  # Give server time to start