import time
import smtpd
import asyncore
import email
import io

import mimetypes
import cgi
import json
import http.server
import threading

import urllib.parse
import socketserver
import datetime

import pkgutil
import mimetypes 

import urllib.request
import urllib.parse

class Mail(object):

    def __init__(self, data):
        msg = email.message_from_string(data)
        
        self.source = data
        self.id = msg.get('Message-ID')
        self.date = self.get_format_date(msg.get('Date'))
        self.sender = self.decode(msg.get('From'))
        self.subject = self.decode(msg.get('Subject'))
        self.to = [to.strip() for to in self.decode(msg.get('To')).split(',')]
        self.cc = [cc.strip() for cc in self.decode(msg.get('Cc', '')).split(',')]
        self.bcc = [bcc.strip() for bcc in self.decode(msg.get('Bcc', '')).split(',')]
        self.body = ''
        self.attachments = {}

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue

            filename = part.get_filename()
            if not filename:
                self.body = self.decode_body(part)
                continue

            self.attachments[filename] = io.BytesIO(part.get_payload(decode=1))

    def get_format_date(self, date_string):
        # http://www.faqs.org/rfcs/rfc2822.html
        format_pattern = '%a, %d %b %Y %H:%M:%S'

        # 3 Jan 2012 17:58:09という形式でくるパターンもあるので、
        # 先頭が数値だったらパターンを変更
        if date_string[0].isdigit():
            format_pattern = '%d %b %Y %H:%M:%S'
        st = time.strptime(date_string[0:-6], format_pattern)
        return datetime.datetime(*st[:6])

    def decode(self, dec_target):
        decodefrag = email.header.decode_header(dec_target)

        value = ''
        for frag, enc in decodefrag:
            if not enc:
                enc = 'utf-8'

            if type(frag) is bytes:
                value += frag.decode(enc)
            else:
                value += frag

        return value

    def decode_body(self, part):
        body = ''
        charset = str(part.get_content_charset())
        if charset:
            body = part.get_payload(decode=1).decode(charset)
        else:
            body = part.get_payload()

        return body


class CustomSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        url = 'http://localhost:8025/api/v2/messages'
        if type(data) is str:
            data = data.encode('utf-8')
        urllib.request.urlopen(url, data).read()


class MyHandler(http.server.SimpleHTTPRequestHandler):

    _messages = []

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/v1/messages':
            items = []
            for mail in self._messages:
                items.append({
                    'ID': mail.id,
                    'from': mail.sender,
                    'to': mail.to,
                    'subject': mail.subject,
                    'date': mail.date.strftime("%Y/%m/%d %H:%M:%S"),
                    'size': len(mail.source),
                })

            self._write(json.dumps({
                'items': items,
                'total': len(self._messages)
            }))
        elif parsed.path.startswith('/api/v1/messages/'):
            mail_id = urllib.parse.unquote(parsed.path.split('/')[-1])
            mail = self._find_mail(mail_id)
            if mail:
                self._write(json.dumps(self._mail2hash(mail)))

        elif parsed.path.startswith('/api/v1/download/'):
            mail_id, filename = [urllib.parse.unquote(item) for item in parsed.path.split('/')][-2:]
            mail = self._find_mail(mail_id)
            tmpfile = mail.attachments[filename]

            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', 'attachment; filename="'+filename+'"')
            self.send_header('Content-Length', len(tmpfile.getvalue()))
            self.end_headers()
            self.wfile.write(tmpfile.getvalue())


        elif parsed.path == '/':
            response = pkgutil.get_data('assets', 'index.html')
            self.send_response(200)
            self.send_header('Content-type', 'text/html;charset=utf-8')
            self.send_header('Content-Length', len(response))
            self.end_headers()
            self.wfile.write(response)

        elif parsed.path.startswith('/assets/'):
            content_type = mimetypes.guess_type(parsed.path)[0]
            response = pkgutil.get_data('assets', parsed.path[7:])
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-Length', len(response))
            self.end_headers()
            self.wfile.write(response)
        
        else:
            super().do_GET()

    # POSTの実装(GETは継承元にある)
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/v2/messages':
            content_len  = int(self.headers.get('content-length'))
            mail = Mail(self.rfile.read(content_len).decode('utf-8'))
            self._messages.insert(0, mail)
            if len(self._messages) > 50:
                self._messages.pop()

            response = json.dumps({'rec':'ok'})

        else:
            self.send_response(500)
            self.end_headers()
            return
        
        # レスポンス作成
        self._write(response)


    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/v1/messages':
            self._messages.clear()

        elif parsed.path.startswith('/api/v1/messages/'):
            mail_id = urllib.parse.unquote(parsed.path.split('/')[-1])
            for i, mail in enumerate(self._messages):
                if mail.id == mail_id:
                    self._messages.pop(i)
                    break

        self.send_response(200)
        self.end_headers()
        

    def _find_mail(self, mail_id):
        for mail in self._messages:
            if mail.id == mail_id:
                return mail

        return None
        
    def _mail2hash(self, mail):
        mail_hash = {
            'ID': mail.id,
            'from': mail.sender,
            'to': mail.to,
            'cc': mail.cc,
            'bcc': mail.bcc,
            'subject': mail.subject,
            'date': mail.date.strftime("%Y/%m/%d %H:%M:%S"),
            'size': len(mail.source),
            'source': mail.source,
            'body': mail.body,
        }

        attachments = []
        for filename, tmpfile in mail.attachments.items():
            attachments.append({
                'filename': filename,
                'size': len(tmpfile.getvalue())
            })

        mail_hash['attachments'] = attachments
        return mail_hash

    def _write(self, response):
        self.send_response(200)
        self.send_header("Content-type", 'application/json')
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))



class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """マルチスレッド化した HTTPServer"""
    pass


def main():

    server = CustomSMTPServer(('0.0.0.0', 1025), None)
    httpd = ThreadedHTTPServer(('0.0.0.0', 8025), MyHandler)
    httpthread = threading.Thread(target=httpd.serve_forever)
    httpthread.start()
    asyncore.loop()

if __name__ == '__main__':
    main()