#!/usr/bin/python2.7
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
import daemon
import lockfile
import argparse

import logging
import sys
import time
import shelve
import signal
import tigerjet
from select import select
from contact_id import handshake
from alarm import Alarm

mynumber = "815"

def collect_alarm_codes(fd):
    logging.info("Collecting Alarm Codes")
    code = ''
    checksum = 0
    codes = []

    # Play the alarm handshake to start getting the codes
    with handshake.Handshake():
        off_hook, digit = get_phone_status(fd)
        while off_hook:
            if digit == -1:
                continue

            # 0 is treated as 10 in the checksum calculation
            checksum += 10 if digit == 0 else digit
            code += format(digit, 'x')
            if len(code) == 16:
                codes.append(((checksum % 15 != 0), code))
                code = ''
                checksum = 0

            off_hook, digit = get_phone_status(fd)

        logging.info("Alarm Hung Up")

    if len(code) != 0:
        # There are leftover bits
        codes.append((True, code))

    return codes

def validate_alarm_call_in(fd, expected):
    number = '000'
    off_hook, digit = get_phone_status(fd)

    if off_hook:
        logging.info("Phone Off The Hook")

    while off_hook:
        if digit != -1:
            logging.debug("Digit %d" % digit)
            number = number[1:] + format(digit, 'x')
            logging.debug("Number %s" % number)

        if number == expected:
            logging.info("Alarm Call In Received")
            break

        off_hook, digit = get_phone_status(fd)
    logging.debug("Number %s" % number)

    if not off_hook:
        logging.info("Phone On The Hook")

    return number == expected and off_hook

def get_phone_status(fd):

    # XXX for python 3 no need to have ORD, can directly read/write
    # values as they are already in bytes
    status = fd.read(2)

    off_hook = ((ord(status[1]) & 0x80) == 0x80)
    digit = ord(status[0])
    if digit < 11:
        digit = digit - 1

    return (off_hook, digit)

def handle_alarm_calling(alarm, fd):
    if validate_alarm_call_in(fd, mynumber):
        codes = collect_alarm_codes(fd)
        alarm.add_new_events(codes)


def init_logging():
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt='%(asctime)s alarmd[%(process)d]: [%(module)s.%(levelname)s] %(message)s',
        datefmt='%b %d %y %I:%M:%S %p')

    log_file = logging.FileHandler('/var/log/alarmd.log')
    log_file.setLevel(logging.INFO)
    log_file.setFormatter(formatter)
    root_logger.addHandler(log_file)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

def alarm_main_loop():
    init_logging()
    logging.info("Started")

    tigerjet.initialize()

    with open('/dev/hidraw0', 'rb') as alarmhid:
        while True:
            # read, write, error
            read, _, _ = select([alarmhid], [], [])

            alarm_config = shelve.open('/alarm_config')
            alarm = alarm_config.get('alarm', Alarm())

            if alarmhid in read:
                handle_alarm_calling(alarm, alarmhid)

            alarm_config['alarm'] = alarm
            alarm_config.close()

    return 0
    
    
def sigcleanup_handler(signum, frame):
    sig_name = next(v for v, k in signal.__dict__.iteritems() if k == signum)
    logging.info("Received %s, exiting" % sig_name)
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(prog='alarmd')
    parser.add_argument('--no-fork', action='store_true', default=False)
    args = parser.parse_args()
    context = daemon.DaemonContext(detach_process=(not args.no_fork),
                                   pidfile=lockfile.FileLock('/var/run/alarmd.pid'),
                                   stderr=(sys.stderr if args.no_fork else None),
                                   stdout=(sys.stdout if args.no_fork else None))
    context.signal_map = { signal.SIGTERM: sigcleanup_handler,
                           signal.SIGINT: sigcleanup_handler }
    with context:
        alarm_main_loop()

if __name__ == "__main__":
    sys.exit(main())
