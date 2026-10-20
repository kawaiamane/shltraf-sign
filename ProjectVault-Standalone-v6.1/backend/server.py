import json,mimetypes,os
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
from .jobs import Manager
from .quick import choose_folder, quick_options
import sys
BASE=(Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent.parent))/'frontend').resolve()
manager=Manager()
dispatcher=None
class Handler(BaseHTTPRequestHandler):
    def json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path.startswith('/api/jobs/'):
            try:self.json(dispatcher("status",path.split('/')[-1]) if dispatcher else manager.status(path.split('/')[-1]))
            except KeyError:self.json({'error':'Not found'},404)
            return
        p=(BASE / (path.lstrip('/') or 'index.html')).resolve()
        if not p.is_relative_to(BASE) or not p.is_file():self.send_error(404);return
        data=p.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(p)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>65536: raise ValueError('Request too large')
            opts=json.loads(self.rfile.read(length))
            path=urlsplit(self.path).path
            if path=='/api/quick-compress':
                folder=choose_folder()
                if not folder:
                    self.json({'cancelled':True});return
                self.json(dispatcher('start',quick_options(folder)) if dispatcher else manager.start('compress',quick_options(folder)),202)
            elif path=='/api/jobs':
                kind=opts.get('kind')
                if kind not in ('compress','extract'):raise ValueError('Invalid kind')
                if not all(isinstance(opts.get(x),str) and opts[x] for x in ('source','target')):raise ValueError('Paths required')
                if kind=='compress' and (not 0<=int(opts.get('level',6))<=9 or not isinstance(opts.get('excludes',[]),list)):raise ValueError('Invalid options')
                self.json(dispatcher("start",opts) if dispatcher else manager.start(kind,opts),202)
            elif path.startswith('/api/cancel/'):
                self.json(dispatcher("cancel",path.split('/')[-1]) if dispatcher else manager.stop(path.split('/')[-1]))
            else:self.json({'error':'Not found'},404)
        except (ValueError,KeyError,TypeError,RuntimeError, json.JSONDecodeError) as e:self.json({'error':str(e)},400)

def main(manager=None, dispatcher=None):
    if manager is not None: globals()["manager"] = manager
    globals()["dispatcher"] = dispatcher
    host='127.0.0.1';port=8765
    print(f'ProjectVault X: http://{host}:{port}',flush=True)
    ThreadingHTTPServer((host,port),Handler).serve_forever()
if __name__=='__main__':main()
