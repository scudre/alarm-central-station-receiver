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

from json import load, dump
from os import remove, path
from shutil import move

from alarm_central_station_receiver.singleton import Singleton
from alarm_central_station_receiver.config import AlarmConfig


def log_event(event):
    skip = ''
    if event['type'] in ['AO', 'AC']:
        skip = '- Automatic event, skipping notification'

    logging.info('%s: %s %s', event['type'], event['description'], skip)


@Singleton
class AlarmStatus(object):
    def __getattr__(self, attr):
        return self._datastore.get(attr)

    def __setattr__(self, attr, value):
        attributes = [
            'arm_status',
            'arm_status_time',
            'auto_arm',
            'history',
            'system_status',
            'active_events']

        if attr in attributes:
            self._datastore[attr] = value
        else:
            super(AlarmStatus._klass, self).__setattr__(attr, value)

    def __init__(self):
        self.datastore_path = AlarmConfig.get('Main', 'data_file_path')
        if not self.load_data():
            self.arm_status = 'disarmed'
            self.arm_status_time = 0
            self.auto_arm = False
            self.system_status = 'ok'
            self.history = []
            self.active_events = {}

    def load_data(self):
        """
        returns True if data loaded from disk, otherwise this is a new
        datafile to initialize
        """
        try:
            logging.info('Loading config from %s', self.datastore_path)
            with open(self.datastore_path, 'r') as file_desc:
                self._datastore = load(file_desc)
                return True
        except (IOError, ValueError):
            self._datastore = {}
            return False

    def save_data(self):
        try:
            logging.info('Saving config to %s', self.datastore_path)
            tmp_path = '.'.join([self.datastore_path, 'tmp'])
            with open(tmp_path, 'w') as file_desc:
                dump(self._datastore, file_desc, sort_keys=True, indent=4)

            move(tmp_path, self.datastore_path)
        except (IOError, OSError) as exc:
            logging.error('Unable to save alarm data: %s', str(exc))
            if path.isfile(tmp_path):
                remove(tmp_path)

    def update_system_status(self):
        """
        Updates system status to be either: ok, alarm, or trouble
        depending on the current outstanding events in the
        `self.outstanding` list.
        """
        event_types = [item['type']
                       for item in self.active_events.values()]
        if 'A' in event_types:
            self.system_status = 'alarm'
        elif 'MA' in event_types or 'T' in event_types:
            self.system_status = 'trouble'
        else:
            self.system_status = 'ok'

    def is_auto_event(self, event):
        return self.auto_arm and self.arm_status in [
            'arming', 'disarming'] and event['type'] in ['O', 'C']

    def mark_auto_event(self, event):
        if not self.is_auto_event(event):
            return None

        event['type'] = 'A' + event['type']
        event['description'] = 'Automatic ' + event['description']
        return event

    def update_arm_status(self, event):
        """
        Updates alarm mode to be either 'disarmed' or 'armed' depending on
        whether an Open or Close event has been received.
        """
        report_type = event['type']
        timestamp = event['timestamp']
        if report_type in ['AO', 'O', 'AC',
                           'C'] and timestamp > self.arm_status_time:
            self.arm_status_time = timestamp
            if report_type in ['AO', 'O']:
                self.arm_status = 'disarmed'
                self.auto_arm = False
            else:
                self.arm_status = 'armed'

    def update_active_events(self, event):
        """
        For the given `event` if applicable either add it or remove
        it from the `self.active_events` list.
        """
        report_type = event['type']
        report_id = event['id']

        # Events to skip tracking.  Opening/Closings are tracked in arm_status, and
        # U is for unknown events which we don't know what to do with
        ignore_list = ['AO', 'O', 'AC', 'C', 'U']
        if not report_type or report_type in ignore_list:
            return

        if report_type == 'R':
            # Restoral, clear any matching events
            self.active_events.pop(report_id, None)
        else:
            self.active_events[report_id] = event

    def add_new_events(self, events):
        if not events:
            logging.info('Home Alarm Calling: Empty Code List!')
        else:
            logging.info('Home Alarm Calling')

        notify_events = []
        for raw_event in events:
            event = self.mark_auto_event(raw_event)
            if not event:
                # If no event was returned, the raw event is not an auto arm/disarm.
                # Only send notifications for non-auto arm/disarms
                event = raw_event
                notify_events.append(event)

            log_event(event)
            self.history.append(event)
            self.update_arm_status(event)
            self.update_active_events(event)

        self.update_system_status()
        self.save_data()

        return notify_events
