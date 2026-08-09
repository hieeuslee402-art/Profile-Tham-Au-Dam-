#!/usr/bin/env python3
"""Server portfolio: tĩnh + API comment (lưu vào comment.json)"""
import json, os, time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'comment.json')

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split('?')[0].rstrip('/') == '/api/comments':
            try:
                with open(DB, encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = []
            # không lộ IP ra ngoài
            return self._json(200, [{'text': e.get('text'), 'ts': e.get('ts')} for e in data[-100:]])
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        if self.path.rstrip('/') != '/api/comments':
            return self._json(404, {'ok': False})
        try:
            ln = int(self.headers.get('Content-Length', '0'))
            d = json.loads(self.rfile.read(ln).decode('utf-8', 'ignore') or '{}')
            text = (d.get('text') or '').strip()[:180]
            if not text:
                return self._json(400, {'ok': False})
            try:
                with open(DB, encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = []
            # mỗi IP chỉ được gửi 1 tin nhắn
            ip = (self.headers.get('X-Forwarded-For') or self.client_address[0]).split(',')[0].strip()
            if any(e.get('ip') == ip for e in data):
                return self._json(429, {'ok': False, 'reason': 'limit'})
            data.append({'text': text, 'ts': int(time.time()), 'ip': ip})
            data = data[-200:]
            with open(DB, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            return self._json(200, {'ok': True, 'total': len(data)})
        except Exception:
            return self._json(500, {'ok': False})

    def log_message(self, *a):
        pass

if __name__ == '__main__':
    print('Serving on http://0.0.0.0:8080')
    ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
