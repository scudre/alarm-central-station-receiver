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
import shelve
import signal
import tigerjet

from os import geteuid
from sys import stderr, stdout
from select import select
from contact_id import handshake, decoder
from alarm import Alarm
from alarm_call import handle_alarm_calling
from alarm_config import AlarmConfig
from notifications import notify, notify_test


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


def update_alarm_events(events):
    alarm_config = shelve.open('/alarm_config')
    alarm = alarm_config.get('alarm', Alarm())
    alarm.add_new_events(events)
    alarm_config['alarm'] = alarm
    alarm_config.close()


def wait_for_alarm(alarmhid):
    read = []
    # read, write, error
    while alarmhid not in read:
        read, _, _ = select([alarmhid], [], [])
        if alarmhid not in read:
            logging.info('alarmhid not in select, ignoring call')


def alarm_main_loop():
    init_logging()
    phone_number = AlarmConfig.get('AlarmSystem', 'phone_number')
    with open(tigerjet.hidraw_path(), 'rb') as alarmhid:
        logging.info("Ready, listening for alarms")
        while True:
            wait_for_alarm(alarmhid)
            raw_events = handle_alarm_calling(alarmhid, phone_number)
            events = decoder.decode(raw_events)
            update_alarm_events(events)
            notify(events)

    return 0


def sigcleanup_handler(signum, _):
    sig_name = next(v for v, k in signal.__dict__.iteritems() if k == signum)
    logging.info("Received %s, exiting" % sig_name)
    sys.exit(0)


def check_running_root():
    if geteuid() != 0:
        stderr.write("Error: Alarmd must run as root - exiting\n")
        sys.exit(-1)


def create_or_check_required_config(path):
    if not AlarmConfig.exists(path):
        stdout.write('Configuration missing, writing to %s.\n\n' % path)
        AlarmConfig.create(path)

    AlarmConfig.load(path)
    missing_config = AlarmConfig.validate(AlarmConfig.get())
    if missing_config:
        stderr.write(
            'Error: The following required configuration is missing from %s\n\n' %
            path)
        stderr.write('\n'.join(missing_config))
        stderr.write('\n\nExiting\n\n')
        sys.exit(-1)


def initialize(config_path):
    check_running_root()
    create_or_check_required_config(config_path)
    tigerjet.initialize()
    handshake.initialize()


def write_config_exit(config_path):
    check_running_root()

    if not AlarmConfig.exists(config_path):
        stdout.write('Writing configuration to %s and exiting.\n' %
                     config_path)
        AlarmConfig.create(config_path)
    else:
        stdout.write(
            'Configuration at %s already exists, skipping write\n' % config_path)

    sys.exit(0)


def notification_test_exit():
    stdout.write('Sending notification.\n')
    notify_test()
    stdout.write('Notification test complete, exiting.\n')
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(prog='alarmd')
    parser.add_argument(
        '--no-fork',
        action='store_true',
        default=False,
        help='Run alarmd in the foreground, useful for debugging')
    parser.add_argument('-c', '--config',
                        default='/etc/alarmd_config.ini',
                        metavar='config_path',
                        dest='config_path',
                        help='Alarm config file path and filename')
    parser.add_argument('--create-config',
                        action='store_true',
                        default=False,
                        help='Create new alarm config file, and exit.')
    parser.add_argument('--notification-test',
                        action='store_true',
                        default=False,
                        help='Send a test notification, and exit.')
    args = parser.parse_args()
    if args.create_config:
        write_config_exit(args.config_path)

    logging.info(
        "Starting in %s mode" %
        'no-fork' if args.no_fork else 'daemonized')
    initialize(args.config_path)
    context = daemon.DaemonContext(
        detach_process=(
            not args.no_fork),
        pidfile=lockfile.FileLock('/var/run/alarmd.pid'),
        stderr=(
            sys.stderr if args.no_fork else None),
        stdout=(
            sys.stdout if args.no_fork else None))
    context.signal_map = {signal.SIGTERM: sigcleanup_handler,
                          signal.SIGINT: sigcleanup_handler}

    if args.notification_test:
        notification_test_exit()

    with context:
        alarm_main_loop()


if __name__ == "__main__":
    sys.exit(main())
