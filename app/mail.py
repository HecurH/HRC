import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from config import mail_settings, mail_text_warn
from config import mail_text_register


class Mail:
    def __init__(self):
        self.context = ssl.create_default_context()

    def register(self, recipient, username, password, pk):
        message = MIMEMultipart()
        message["From"] = mail_settings['email']
        message["To"] = recipient
        message["Subject"] = 'Регистрация в HRC'
        message["Bcc"] = recipient

        message.attach(MIMEText(mail_text_register.replace('[логин]', username).replace('[пароль]', password), "plain"))
        part = MIMEBase("application", "octet-stream")
        part.set_payload(pk)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= privkey.pem",
        )

        message.attach(part)
        text = message.as_string()

        server = smtplib.SMTP_SSL(mail_settings['server'], mail_settings['port'], context=self.context)
        server.login(mail_settings['email'], mail_settings['password'])
        server.sendmail(mail_settings['email'], recipient, text)
        server.quit()

    def warn(self, recipient, ip):
        message = MIMEMultipart()
        message["From"] = mail_settings['email']
        message["To"] = recipient
        message["Subject"] = 'Подозрительная попытка входа'
        message["Bcc"] = recipient

        url = "http://ip-api.com/json/"+ip

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        message.attach(MIMEText(mail_text_warn.replace('[ip]', ip).replace('[loc]', f"{data.get('country')}, {data.get('city')}"), "plain"))

        text = message.as_string()

        server = smtplib.SMTP_SSL(mail_settings['server'], mail_settings['port'], context=self.context)
        server.login(mail_settings['email'], mail_settings['password'])
        server.sendmail(mail_settings['email'], recipient, text)
        server.quit()
