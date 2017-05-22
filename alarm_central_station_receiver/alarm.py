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
import RPi.GPIO as GPIO
from json import dumps
from collections import deque
from contact_id import dsc
from notifications import notify

class Alarm(object):
    def __init__(self):
        self.alarm_mode = "stay"
        self.system_status = "ok"
        self.history = deque()
        self.outstanding = {}
        self._initialize_rpi_gpio()

    def _update_system_status(self):
        """
        Updates system status to be either: ok, alarm, or trouble
        depending on the current outstanding events in the
        `self.outstanding` list.
        """
        self.system_status = 'ok'
        for entry in self.outstanding.itervalues():
            if entry['type'] == 'A':
                self.system_status = 'alarm'
                break

            if entry['type'] == 'MA' or entry['type'] == 'T':
                self.system_status = 'trouble'

    def _update_alarm_mode(self, entry):
        """
        Updates alarm mode to be either 'disarmed' or 'stay' depending on
        whether an Open or Close event has been received.
        """
        report_type = entry['type']
        if report_type == 'O':
            self.alarm_mode = 'disarmed'
        elif report_type == 'C':
            self.alarm_mode = 'stay'

    def _update_outstanding_events(self, entry):
        """
        For the given `entry` if applicable either add it or remove
        it from the `self.outstanding` list.
        """
        report_type = entry['type']
        report_id = entry['id']
        if report_type == 'R':
            # Restoral, remove any matching reports from
            # the outstanding event list
            self.outstanding.pop(report_id, None)
        elif report_type and report_type not in ['O', 'C', 'U']:
            # Opening/Closings are treated separately, dont add them
            # to the outstanding list

            if report_id not in ['627000', '628000', '411000', '412000']:
                # Finally, skip listing the DLS/Installer
                # Lead In/Out as an alarm
                self.outstanding[report_id] = entry

    def add_new_events(self, codes):
        curr_time = time.strftime("%b %d %I:%M:%S %p")
        email_codes = []

        for err, code in codes:
            if not err:
                report_type, description = dsc.digits_to_alarmreport(code)
                email_codes.append('%s: %s' % (report_type, description))
            else:
                report_type = 'U'
                if len(code) != 16:
                    description = \
                        'Leftover Bits: %s (len %d)' % (code, len(code))
                else:
                    description = \
                        'Checksum Mismatch: %s' % code
                email_codes.append(description)

            new_entry = {'timestamp' : curr_time,
                         'type' : report_type,
                         'description' : description,
                         'id' : code[7:10] + code[12:15],
                         }

            self.history.appendleft(new_entry)
            self._update_alarm_mode(new_entry)
            self._update_outstanding_events(new_entry)

        self._update_system_status()

        if email_codes:
            # Send notifications if any configured
            logging.info("Home Alarm Calling:\n%s" % '\n'.join(email_codes))
            notify(email_codes)
        else:
            logging.info("Empty Code List!")

    def json_history(self, start_index, stop_index):
        hist_slice = []
        length = len(self.history)

        if length >= start_index:
            # XXX enumerate func?
            idx = max(start_index, 0)
            while idx < min(stop_index, length):
                hist_slice.append(self.history[idx])
                idx += 1

        return dumps(hist_slice)

    def json_state(self):
        outstanding_json = [entry for entry in self.outstanding.itervalues()]
        state = {'mode' : self.alarm_mode,
                 'status' : self.system_status,
                 'outstanding_events' : outstanding_json,
                 }

        return dumps(state)

    def arm(self, mode='stay'):
        if self.alarm_mode not in ['stay', 'away', 'arming']:
            self._trip_keyswitch()
            self.alarm_mode = 'arming'

    def disarm(self):
        if self.alarm_mode not in ['disarmed', 'disarming']:
            self._trip_keyswitch()
            if self.alarm_mode == 'arming':
                self.alarm_mode = 'disarmed'
            else:
                self.alarm_mode = 'disarming'

    def _trip_keyswitch(self):
        """
        This pin is connected to an I/O port on the PC9155 alarm.
        The I/O port is configured in the PC9155 as a 'temporary
        keyswitch'. Toggling this I/O port triggers the alarm
        to arm and disarm.
        """
        GPIO.output(15, not GPIO.input(15))
        time.sleep(2)
        GPIO.output(15, not GPIO.input(15))

    def _initialize_rpi_gpio(self):
        """
        This pin is connected to an I/O port on the PC9155 alarm.
        The I/O port is configured in the PC9155 as a 'temporary
        keyswitch'. Toggling this I/O port triggers the alarm
        to arm and disarm.
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(15, GPIO.OUT)
