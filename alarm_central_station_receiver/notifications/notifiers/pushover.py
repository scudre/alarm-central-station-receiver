"""
Copyright (2018) Chris Scuderi

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
import requests
from alarm_central_station_receiver.config import AlarmConfig


def create_message(events):
    """
    Build the message.  The first event's timestamp is returned as the
    overall event timestamp.
    """
    messages = [event.get('description') for event in events]
    return (events[0].get('timestamp'), '\n'.join(messages))


def create_params(events):
    timestamp, message = create_message(events)
    data = {
        'token': AlarmConfig.config.get('PushoverNotification', 'token'),
        'user': AlarmConfig.config.get('PushoverNotification', 'user'),
        'timestamp': timestamp,
        'title': 'Alarm Notification',
        'message': message,
    }

    device = AlarmConfig.config.get('PushoverNotification', 'device', fallback=None)
    if device:
        data['device'] = device

    priority = AlarmConfig.config.get('PushoverNotification', 'priority', fallback=None)
    if priority:
        data['priority'] = priority

    return data


def notify(events):
    if not events:
        return

    if 'PushoverNotification' not in AlarmConfig.config:
        return

    logging.info("Sending pushover notification...")

    data = create_params(events)
    pushover_uri = 'https://api.pushover.net/1/messages.json'
    response = requests.post(pushover_uri, data=data)
    if response.status_code == 200:
        logging.info("Sending complete")
    else:
        err_list = response.json().get('errors')
        status_code = response.status_code
        logging.error('Error sending pushover notification HTTP %s: %s',
                      status_code, ', '.join(err_list))
