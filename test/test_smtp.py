import base64
import smtplib
import ssl
from email.mime.text import MIMEText
from email.utils import formatdate

import time


main_text = "本文の確認テスト"
msg = MIMEText(main_text, "plain", 'utf-8')

msg["Subject"] = "件名のテスト"
msg["From"] = "from@example.com"
msg["To"] = "to@example.com"
msg["Cc"] = ""
msg["Bcc"] = ""
msg["Date"] = formatdate(None,True)
msg["Message-ID"] = str(time.time())

smtpclient = smtplib.SMTP('localhost', 1025)
smtpclient.send_message(msg)
smtpclient.quit()
