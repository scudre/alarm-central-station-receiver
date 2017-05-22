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

contact_info = {
    'user' : '',
    'password' : '',
    'to' : '',
    'server' : '',
    'port' : 587
}

def send_email(message):
    logging.info("Sending Email...")

    msg = MIMEMultipart('alternative')
    msg['From'] = contact_info['user']
    msg['To'] = contact_info['to']
    body = "%s:\n%s" % (time.strftime("%b %d %I:%M:%S %p"), '\n'.join(message))
    msg.attach(MIMEText(body, 'plain'))
    msg.attach(MIMEText(body, 'html'))

    s = smtplib.SMTP(contact_info['server'], contact_info['port'])
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(contact_info['user'], contact_info['password'])
    s.sendmail(contact_info['user'], [contact_info['to']], msg.as_string())
    s.quit()

    logging.info("Email Send Complete")


def send_email_async(message):
    """
    Send email asynchrnously
    """
    p = multiprocessing.Process(target=send_email, args=(message,))
    p.start()
