import asyncio
import io
import mimetypes
import os
import shutil

from http import HTTPStatus

class WebServerProtocol(asyncio.Protocol):

    def __init__(self):
        class Response():
            def __init__(self):
                self.headers = []
                self.body = io.BytesIO()
        
        self.response = Response()
        

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        raw_request = data.decode()

        # Data received:
        request = self.parse_request(raw_request)

        mname = 'do_' + request.method
        if not hasattr(self, mname):
            self.send_error(HTTPStatus.METHOD_NOT_ALLOWED, 'Method Not Allowed {}'.format(request.method))
            return

        # 各メソッドに応じた処理
        method = getattr(self, mname)
        method(request)

        self.send(HTTPStatus.OK)


    def parse_request(self, raw_request):
        class Request():
            def __init__(self, raw_request):
                self.raw_headers = raw_request.split('\r\n')
                method, path = self.raw_headers[0].split()[:2]
                self.method = method.upper()
                self.path = path
                self.body = self.raw_headers[-1] # 最終行がブラウザからの送信データ

        return Request(raw_request)

    def set_header(self, name, value):
        self.response.headers.append((name, value))

    def write(self, body):
        if isinstance(body ,str):
            body = body.encode('utf-8')
        self.response.body.write(body)

    def do_GET(self, request):
        # カレントディレクトリが対象 pathは先頭のスラッシュを除去
        request_file = os.path.join(os.getcwd(), request.path[1:])
        # リクエストされたファイルが存在しない
        if not os.path.isfile(request_file):
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        # mimetypeを判定
        content_type, _ = mimetypes.guess_type(request_file)
        if not content_type: # 不明な場合
            content_type = 'application/octet-stream'

        self.set_header('Content-Type', content_type)
        with open(request_file, 'rb') as f:
            shutil.copyfileobj(f, self.response.body)


    def do_POST(self, request):
        pass

    def do_DELETE(self, request):
        pass

    def send_error(self, status, message=None):
        if not message:
            message = status.description
        self.write(message)
        self.send(status)

    def send(self, status):
        # 出力するサイズを確定
        self.set_header('Content-Length', self.response.body.getbuffer().nbytes)
        # ヘッダー出力
        self.transport.write('HTTP/1.1 {} {}\r\n'.format(status.value, status.phrase).encode('utf-8'))
        for name, value in  self.response.headers:
            self.transport.write('{}: {}\r\n'.format(name, value).encode('utf-8'))

        # データ出力
        self.transport.write('\r\n'.encode('utf-8'))
        self.transport.write(self.response.body.getbuffer())
        print('Close the client socket')
        self.transport.close()

