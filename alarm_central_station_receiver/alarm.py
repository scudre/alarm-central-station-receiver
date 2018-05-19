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
from json import load, dump
import os.path
from os import remove
from shutil import move

from singleton import Singleton
from alarm_config import AlarmConfig


class AlarmSystem(Singleton):
    @staticmethod
    def _trip_keyswitch():
        """
        This pin is connected to an I/O port on the PC9155 alarm.
        The I/O port is configured in the PC9155 as a 'temporary
        keyswitch'. Toggling this I/O port triggers the alarm
        to arm and disarm.
        """
        RPi.GPIO.output(15, not GPIO.input(15))
        time.sleep(2)
        RPi.GPIO.output(15, not GPIO.input(15))

    @staticmethod
    def _initialize_rpi_gpio():
        """
        This pin is connected to an I/O port on the PC9155 alarm.
        The I/O port is configured in the PC9155 as a 'temporary
        keyswitch'. Toggling this I/O port triggers the alarm
        to arm and disarm.
        """
        RPi.GPIO.setwarnings(False)
        RPi.GPIO.setmode(GPIO.BOARD)
        RPi.GPIO.setup(15, GPIO.OUT)

    def __init__(self):
        self.alarm = AlarmHistory()
        if AlarmConfig.get('AlarmSystem', 'alarmd_arm_disarm'):
            import RPi
            self._initialize_rpi_gpio()

    def arm(self):
        if self.alarm.arm_status in ['disarmed', 'disarming']:
            self._trip_keyswitch()
            self.alarm.arm_status = 'arming'

    def disarm(self):
        if self.alarm.arm_status in ['arming', 'armed']:
            self._trip_keyswitch()

            # If the system wasn't fully armed, there won't be an event
            # from the alarm indicating arm/disrm
            if self.alarm.arm_status == 'arming':
                self.alarm.arm_status = 'disarmed'
            else:
                self.alarm.arm_status = 'disarming'


class AlarmHistory(Singleton):
    def __getattr__(self, attr):
        return self._datastore.get(attr)

    def __setattr__(self, attr, value):
        attributes = [
            'arm_status', 'arm_status_time', 'history', 'system_status', 'active_events'
        ]

        if attr in attributes:
            self._datastore[attr] = value
        else:
            super(AlarmHistory, self).__setattr__(attr, value)

    def __init__(self):
        self.datastore_path = AlarmConfig.get('AlarmSystem', 'data_file')
        self.datastore_path = 'test'
        if not self.load_data():
            self.arm_status = 'disarmed'
            self.arm_status_time = 0
            self.system_status = 'ok'
            self.history = []
            self.active_events = {}

    def load_data(self):
        """
        returns True if data loaded from disk, otherwise this is a new
        datafile to initialize
        """
        try:
            print self.datastore_path
            with open(self.datastore_path, 'r') as file_desc:
                self._datastore = load(file_desc)
                return True
        except (IOError, ValueError):
            self._datastore = {}
            return False

    def save_data(self):
        try:
            tmp_path = '.'.join([self.datastore_path, 'tmp'])
            with open(tmp_path, 'w') as file_desc:
                dump(self._datastore, file_desc)

            move(tmp_path, self.datastore_path)
        except (IOError, OSError) as exc:
            logging.error('Unable to save alarm data: %s', str(exc))
            if os.path.isfile(tmp_path):
                remove(tmp_path)

    def update_system_status(self):
        """
        Updates system status to be either: ok, alarm, or trouble
        depending on the current outstanding events in the
        `self.outstanding` list.
        """
        event_types = [item['type']
                       for item in self.active_events.itervalues()]
        if 'A' in event_types:
            self.system_status = 'alarm'
        elif 'MA' in event_types or 'T' in event_types:
            self.system_status = 'trouble'
        else:
            self.system_status = 'ok'

    def update_arm_status(self, event):
        """
        Updates alarm mode to be either 'disarmed' or 'armed' depending on
        whether an Open or Close event has been received.
        """
        report_type = event['type']
        timestamp = event['timestamp']
        if report_type in ['O', 'C'] and timestamp > self.arm_status_time:
            self.arm_status_time = timestamp
            if report_type == 'O':
                self.arm_status = 'disarmed'
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
        ignore_list = ['O', 'C', 'U']
        if not report_type or report_type in ignore_list:
            return

        if report_type == 'R':
            # Restoral, clear any matching events
            self.active_events.pop(report_id, None)
        else:
            self.active_events[report_id] = event

    def add_new_events(self, events):
        for event in events:
            self.history.append(event)
            self.update_arm_status(event)
            self.update_active_events(event)

        self.update_system_status()
        self.save_data()
