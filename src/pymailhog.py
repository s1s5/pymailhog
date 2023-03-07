import argparse
import asyncio
import datetime
import email
import io
import json
import mimetypes 
import pkgutil
import time
import urllib.parse
import uuid

from http import HTTPStatus

from smtphog import SMTPServerProtocol
from httphog import WebServerProtocol

__version__ = '0.0.4'

class Mail(object):

    def __init__(self, data):
        msg = email.message_from_string(data)
        
        self.source = data
        self.id = msg.get('Message-ID') or uuid.uuid4().hex
        if msg.get('Date'):
            self.date = self.get_format_date(msg.get('Date'))
        else:
            self.date = datetime.datetime.utcnow()
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


class CustomSMTPServer(SMTPServerProtocol):
    def __init__(self, messages):
        super().__init__()
        self._messages = messages
        
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        if isinstance(data, bytes):
            data = data.decode('utf-8')

        mail = Mail(data)
        self._messages.insert(0, mail)
        if len(self._messages) > 50:
            self._messages.pop()


class MyHandler(WebServerProtocol):

    def __init__(self, messages):
        super().__init__()
        self._messages = messages

    def do_GET(self, request):
        parsed = urllib.parse.urlparse(request.path)
        if parsed.path == '/api/messages':
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
        elif parsed.path.startswith('/api/messages/'):
            mail_id = urllib.parse.unquote(parsed.path.split('/')[-1])
            mail = self._find_mail(mail_id)
            if mail:
                self._write(json.dumps(self._mail2hash(mail)))

        elif parsed.path.startswith('/api/download/'):
            mail_id, filename = [urllib.parse.unquote(item) for item in parsed.path.split('/')][-2:]
            mail = self._find_mail(mail_id)
            tmpfile = mail.attachments[filename]

            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', 'attachment; filename="'+filename+'"')
            self.set_header('Content-Length', len(tmpfile.getvalue()))
            self.write(tmpfile.getvalue())


        elif parsed.path == '/':
            response = pkgutil.get_data('assets', 'index.html')
            self.set_header('Content-type', 'text/html;charset=utf-8')
            self.write(response)

        elif parsed.path.startswith('/assets/'):
            content_type = mimetypes.guess_type(parsed.path)[0]
            response = pkgutil.get_data('assets', parsed.path[7:])
            self.set_header('Content-type', content_type)
            self.write(response)
        
        else:
            super().do_GET(request)

    # POSTの実装(GETは継承元にある)
    def do_POST(self, request):
        pass


    def do_DELETE(self, request):
        parsed = urllib.parse.urlparse(request.path)
        if parsed.path == '/api/messages':
            self._messages.clear()

        elif parsed.path.startswith('/api/messages/'):
            mail_id = urllib.parse.unquote(parsed.path.split('/')[-1])
            for i, mail in enumerate(self._messages):
                if mail.id == mail_id:
                    self._messages.pop(i)
                    break
        

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
        self.set_header('Content-type', 'application/json')
        self.set_header('Content-Length', len(response))
        self.write(response)



def args_parser():
    parser = argparse.ArgumentParser(description='PyMailHog テスト環境でのメール確認用stmpサーバー')

    parser.add_argument(
        '-v', '--version', action='version', version='PyMailHog {}'.format(__version__)
    )

    parser.add_argument(
        '-sp', '--smtpport', type=int, default=1025, help='smtpサーバーのポート番号 default:1025'
    )

    parser.add_argument(
        '-hp', '--httpport', type=int, default=8025, help='httpサーバーのポート番号 default:8025'
    )

    return parser

async def main():
    parser = args_parser()
    args = parser.parse_args()

    # SMTP / HTTPで共有するメールデータ
    messages = []

    loop = asyncio.get_running_loop()

    await loop.create_server(
        lambda: CustomSMTPServer(messages),
        '0.0.0.0', args.smtpport)

    server = await loop.create_server(
        lambda: MyHandler(messages),
        '0.0.0.0', args.httpport)

    print('Listen smtp port: %d, http port: %d' % (args.smtpport, args.httpport))
    async with server:
        await server.serve_forever()
    

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('stop server')
