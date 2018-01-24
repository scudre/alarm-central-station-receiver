"""
Copyright (2017) Chris Scuderi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
import time
import multiprocessing
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..alarm_config import AlarmConfig


def send_email(message):
    logging.info("Sending Email...")
    username = AlarmConfig.get('EmailNotification', 'username')
    password = AlarmConfig.get('EmailNotification', 'password')
    to_addr = AlarmConfig.get('EmailNotification', 'notification_email')
    subject = AlarmConfig.get('EmailNotification', 'notification_subject')
    tls = AlarmConfig.get('EmailNotification', 'tls')
    server = AlarmConfig.get('EmailNotification', 'server_address')
    server_port = AlarmConfig.get('EmailNotification', 'port')

    msg = MIMEMultipart('alternative')
    msg['From'] = username
    msg['To'] = to_addr
    mst['Subject'] = subject
    body = "%s:\n%s" % (time.strftime("%b %d %I:%M:%S %p"), '\n'.join(message))
    msg.attach(MIMEText(body, 'plain'))
    msg.attach(MIMEText(body, 'html'))

    s = smtplib.SMTP(server, server_port)
    s.ehlo()
    if bool(tls) == True:
    	s.starttls()
    s.ehlo()
    s.login(username, password)
    s.sendmail(username, [to_addr], msg.as_string())
    s.quit()

    logging.info("Email Send Complete")


def send_email_async(message):
    """
    Send email asynchrnously
    """
    p = multiprocessing.Process(target=send_email, args=(message,))
    p.start()
