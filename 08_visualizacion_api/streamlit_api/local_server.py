"""Simula API Gateway en local (puerto 3000) llamando a la misma Lambda. Solo para pruebas."""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse

sys.path.insert(0, "lambda")
import handler  # noqa: E402


class Gateway(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)
        event = {"rawPath": u.path, "queryStringParameters": dict(parse_qsl(u.query)),
                 "requestContext": {"http": {"method": "GET"}}}
        r = handler.lambda_handler(event, None)
        self.send_response(r["statusCode"])
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(r["body"].encode("utf-8"))


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 3000), Gateway).serve_forever()
