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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from alarm_central_station_receiver.config import AlarmConfig


def create_message(events):
    """
    Build the message body.  The first event's timestamp is included
    in the message body as well.  When sending this email to an SMS bridge,
    sometimes the time that the SMS is received is well after the event occurred
    and there is no clear way to know when the message was actually sent.
    """
    messages = []
    timestamp = ''
    for event in events:
        rtype = event.get('type')
        desc = event.get('description')
        if not timestamp:
            timestamp = event.get('timestamp')

        messages.append('%s: %s' % (rtype, desc))

    return '%s:\n%s' % (timestamp, '\n'.join(messages))


def notify(events):
    if not events:
        return

    if 'EmailNotification' not in AlarmConfig.config:
        return

    logging.info("Sending email...")
    username = AlarmConfig.config.get('EmailNotification', 'username')
    password = AlarmConfig.config.get('EmailNotification', 'password')
    to_addr = AlarmConfig.config.get('EmailNotification', 'notification_email')
    subject = AlarmConfig.config.get('EmailNotification', 'notification_subject')
    tls = AlarmConfig.config.getboolean('EmailNotification', 'tls')
    server = AlarmConfig.config.get('EmailNotification', 'server_address')
    server_port = AlarmConfig.config.get('EmailNotification', 'port')

    msg = MIMEMultipart('alternative')
    msg['From'] = username
    msg['To'] = to_addr
    msg['Subject'] = subject
    body = create_message(events)
    msg.attach(MIMEText(body, 'plain'))
    msg.attach(MIMEText(body, 'html'))

    try:
        s = smtplib.SMTP(server, server_port)
        s.ehlo()
        if tls:
            s.starttls()
        s.ehlo()
        s.login(username, password)
        s.sendmail(username, [to_addr], msg.as_string())
        s.quit()
        logging.info("Email send complete")
    except smtplib.SMTPException as exc:
        logging.error("Error sending email: %s", str(exc))
