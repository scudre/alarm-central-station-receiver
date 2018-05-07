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
from email_notify import send_email_async


def log_events(events):
    if not events:
        logging.info('Empty Code List!')
    else:
        messages = []
        for event in events:
            rtype = event.get('type')
            desc = event.get('description')
            messages.append('%s: %s' % (rtype, desc))

        logging.info("Home Alarm Calling:\n%s", ', '.join(messages))

def notify_test():
    events = [
        {
            'timestamp' : time.strftime("%b %d %I:%M:%S %p"),
            'type' : 'Test',
            'description' : 'This is test event #1',
            'id' : '1'
        },
        {
            'timestamp' : time.strftime("%b %d %I:%M:%S %p"),
            'type' : 'Test',
            'description' : 'This is test event #2',
            'id' : '2'
        }
        ]

    notify(events)
            
        
def notify(events):
    # List of notifications to pass events to
    log_events(events)
    send_email_async(events)
