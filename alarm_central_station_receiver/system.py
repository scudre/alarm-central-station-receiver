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
import time

from alarm_central_station_receiver.singleton import Singleton
from alarm_central_station_receiver.config import AlarmConfig
from alarm_central_station_receiver.status import AlarmStatus
from alarm_central_station_receiver.events import create_event


try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


@Singleton
class AlarmSystem(object):
    def valid_setup(self):
        if not self.pin:
            return False

        if not GPIO:
            logging.error(
                'Python package RPi.GPIO must be installed to arm/disarm via RaspberryPi GPIO pins')
            return False

        return True

    def _trip_keyswitch(self):
        """
        This pin is connected to an I/O port on the PC9155 alarm.
        The I/O port is configured in the PC9155 as a 'temporary
        keyswitch'. Toggling this I/O port triggers the alarm
        to arm and disarm.
        """
        GPIO.output(self.pin, not GPIO.input(self.pin))
        time.sleep(2)
        GPIO.output(self.pin, not GPIO.input(self.pin))

    def _initialize_rpi_gpio(self):
        """
        This pin is connected to an I/O port on the PC9155 alarm.
        The I/O port is configured in the PC9155 as a 'temporary
        keyswitch'. Toggling this I/O port triggers the alarm
        to arm and disarm.
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)

    def __init__(self):
        self.alarm = AlarmStatus()
        self.pin = AlarmConfig.config.getint('RpiArmDisarm',
                                             'gpio_pin',
                                             fallback=None)
        if not self.valid_setup():
            return

        self._initialize_rpi_gpio()

    def arm(self, auto_arm):
        if not self.valid_setup():
            return None

        if self.alarm.arm_status in ['armed', 'arming']:
            status = 'System already %s, ignoring request' % self.alarm.arm_status
            logging.info(status)
            return status

        status = 'Arming system%s...' % (' in auto mode' if auto_arm else '')
        logging.info(status)

        self._trip_keyswitch()
        self.alarm.arm_status = 'arming'
        self.alarm.auto_arm = auto_arm
        self.alarm.save_data()

        return status

    def disarm(self, auto_arm):
        if not self.valid_setup():
            return None

        if self.alarm.arm_status in ['disarming', 'disarmed']:
            status = 'System already %s, ignoring request' % self.alarm.arm_status
            logging.info(status)

            return status

        if auto_arm and not self.alarm.auto_arm:
            status = 'System manually armed, skipping auto disarm'
            logging.info(status)
            return status

        status = 'Disarming system...'
        logging.info(status)
        self._trip_keyswitch()

        # If the system wasn't fully armed, there won't be an event
        # from the alarm indicating arm/disarm
        if self.alarm.arm_status == 'arming':
            self.alarm.arm_status = 'disarmed'
            self.alarm.auto_arm = False
        else:
            self.alarm.arm_status = 'disarming'
            self.alarm.auto_arm = auto_arm

        self.alarm.save_data()

        return status

    def abort_arm_disarm(self):
        if self.alarm.arm_status == 'disarming':
            self.alarm.arm_status = 'armed'
            description = 'Unable to Disarm System'
            event_code = '0001'
        elif self.alarm.arm_status == 'arming':
            self.alarm.arm_status = 'disarmed'
            self.alarm.auto_arm = False
            description = 'Unable to Arm System'
            event_code = '0002'
        else:
            logging.info('System is %s, nothing to abort',
                         self.alarm.arm_status)
            return []

        self.alarm.save_data()

        events = [create_event('E', event_code, description, event_code)]
        return self.alarm.add_new_events(events)
