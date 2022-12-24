import smtplib
import email.header
import email.encoders
import email.utils
import email.mime
import email.mime.text
import email.mime.multipart

import urllib.request
import json

import unittest

class TestPyMailHogBasic(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self._delete_message(self)

    @classmethod
    def tearDownClass(self):
        pass
        #self._delete_message(self)

    def test_send_utf8(self):

        main_text = 'UTF-8本文の確認テスト🍣🍺'
        msg = email.mime.text.MIMEText(main_text, 'plain', 'utf-8')

        msg['Subject'] = 'UTF-8件名のテスト🍣🍺'
        msg['From'] = 'from@example.com'
        msg['To'] = 'to@example.com'
        msg['Cc'] = 'cc@example.com'
        msg['Date'] = email.utils.formatdate(None,True)
        msg['Message-ID'] = 'test_send_utf8'
        self._send(msg)

        rmsg = self._get_message(msg['Message-ID'])
        self.assertEqual(msg['Subject'], rmsg['subject'])
        self.assertEqual(msg['From'], rmsg['from'])
        self.assertEqual([msg['To']], rmsg['to'])
        self.assertEqual([msg['Cc']], rmsg['cc'])
        self.assertEqual(main_text, rmsg['body'])


    def test_send_sjis(self):

        main_text = 'iso-2022-jp本文の確認テスト'
        msg = email.mime.text.MIMEText(main_text, 'plain', 'iso-2022-jp')

        subject = 'SJIS件名のテスト'
        msg['Subject'] = email.header.Header(subject, 'iso-2022-jp')
        msg['From'] = 'from@example.com'
        msg['To'] = 'to@example.com'
        msg['Cc'] = 'cc@example.com'
        msg['Date'] = 'Mon, 25 Nov 2019 22:08:09 +0900'
        msg['Message-ID'] = 'test_send_sjis'
        self._send(msg)

        rmsg = self._get_message(msg['Message-ID'])
        self.assertEqual(msg['Subject'], rmsg['subject'])
        self.assertEqual(msg['From'], rmsg['from'])
        self.assertEqual([msg['To']], rmsg['to'])
        self.assertEqual([msg['Cc']], rmsg['cc'])
        self.assertEqual(main_text, rmsg['body'])
        self.assertEqual('2019/11/25 22:08:09', rmsg['date'])


    def test_sent_attachment(self):
        msg = email.mime.multipart.MIMEMultipart()

        msg['Subject'] = '添付ファイルあり'
        msg['From'] = 'from@example.com'
        msg['To'] = 'to@example.com'
        msg['Cc'] = 'cc@example.com'
        msg['Date'] = 'Mon, 25 Nov 2019 07:08:09 +0900'
        msg['Message-ID'] = 'test_sent_attachment'

        main_text = '添付ファイルの送信テスト(UTF8)'
        msg.attach(email.mime.text.MIMEText(main_text, 'plain', 'utf-8'))


        attachment = email.mime.base.MIMEBase('application', 'octet-stream')
        attachment.set_payload('添付ファイルテスト'.encode('utf-8'))
        email.encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment; filename="attachment.txt"')
        msg.attach(attachment)

        self._send(msg)

        rmsg = self._get_message(msg['Message-ID'])
        self.assertEqual(msg['Subject'], rmsg['subject'])
        self.assertEqual(msg['From'], rmsg['from'])
        self.assertEqual([msg['To']], rmsg['to'])
        self.assertEqual([msg['Cc']], rmsg['cc'])
        self.assertEqual(main_text, rmsg['body'])
        self.assertEqual('2019/11/25 07:08:09', rmsg['date'])

        attachments = rmsg['attachments'][0]
        self.assertEqual('attachment.txt', attachments['filename'])
        


    def _get_message(self, msg_id=None):
        url = 'http://localhost:8025/api/messages'
        if msg_id:
            url += '/'+msg_id
        response = urllib.request.urlopen(url)
        body = response.read().decode('utf-8')
        return json.loads(body)

    def _delete_message(self, msg_id=None):
        url = 'http://localhost:8025/api/messages'
        if msg_id:
            url += '/' + msg_id
        req = urllib.request.Request(url, method='DELETE')
        urllib.request.urlopen(req)

    def _send(self, msg):
        smtpclient = smtplib.SMTP('localhost', 1025)
        smtpclient.send_message(msg)
        smtpclient.quit()

if __name__ == '__main__':
    unittest.main()