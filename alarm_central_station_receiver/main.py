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
import signal
import socket

import tigerjet

from os import geteuid
from sys import stderr, stdout
from select import select

import json_ipc
from contact_id import handshake, decoder, callup
from alarm import AlarmHistory, AlarmSystem
from alarm_config import AlarmConfig
from notifications import notify, notify_test


def init_logging():
    root_logger = logging.getLogger('')
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt='%(asctime)s alarmd[%(process)d]: [%(module)s.%(levelname)s] %(message)s',
        datefmt='%b %d %y %I:%M:%S %p')

    console = logging.StreamHandler(stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    log_file = logging.FileHandler('/var/log/alarmd.log')
    log_file.setLevel(logging.INFO)
    log_file.setFormatter(formatter)
    root_logger.addHandler(log_file)

    return log_file.stream


def sigcleanup_handler(signum, _):
    sig_name = next(v for v, k in signal.__dict__.iteritems() if k == signum)
    logging.info("Received %s, exiting", sig_name)
    sys.exit(0)


def check_running_root():
    if geteuid() != 0:
        stderr.write("Error: Alarmd must run as root - exiting\n")
        sys.exit(-1)


def create_or_check_required_config(path):
    if not AlarmConfig.exists(path):
        logging.info('Configuration missing, writing to %s.\n\n', path)
        AlarmConfig.create(path)

    AlarmConfig.load(path)
    missing_config = AlarmConfig.validate(AlarmConfig.get())
    if missing_config:
        logging.error(
            'The following required configuration is missing from %s\n\n', path)
        logging.error('\n'.join(missing_config))
        logging.error('\n\nExiting\n\n')
        sys.exit(-1)


def initialize(config_path):
    create_or_check_required_config(config_path)
    tigerjet.initialize()
    handshake.initialize()


def write_config_exit(config_path):
    if not AlarmConfig.exists(config_path):
        logging.info('Writing configuration to %s and exiting.\n',
                     config_path)
        AlarmConfig.create(config_path)
    else:
        logging.info(
            'Configuration at %s already exists, skipping write\n', config_path)

    sys.exit(0)


def notification_test_exit():
    logging.info('Sending notification.\n')
    notify_test()
    logging.info('Notification test complete, exiting.\n')
    sys.exit(0)


def process_alarm_event(alarmhid, phone_number, alarm_history):
    raw_events = callup.handle_alarm_calling(alarmhid, phone_number)
    events = decoder.decode(raw_events)
    alarm_history.add_new_events(events)
    notify(events)


def process_sock_request(sockfd):
    try:
        conn, _ = sockfd.accept()
        conn.settimeout(20)
        msg = json_ipc.recv(conn)
        command = msg.get('command')
        auto_arm = True if 'auto' in command else False
        if command in ['arm', 'auto-arm']:
            AlarmSystem().arm(auto_arm)
            rsp = {'error': False}
        elif command in ['disarm', 'auto-disarm']:
            AlarmSystem().disarm(auto_arm)
            rsp = {'error': False}
        else:
            rsp = {'error': 'Invalid command %s' % command}

        json_ipc.send(conn, rsp)
        conn.close()

    except socket.timeout:
        logging.error("Timed out receiving data from client")


def alarm_main_loop():
    phone_number = AlarmConfig.get('AlarmSystem', 'phone_number')
    alarm_history = AlarmHistory()

    with open(tigerjet.hidraw_path(), 'rb') as alarmhid:
        with json_ipc.ServerSock() as sockfd:
            logging.info("Ready, listening for alarms")
            while True:
                read = []
                read, _, _ = select([alarmhid, sockfd], [], [])
                if alarmhid in read:
                    process_alarm_event(alarmhid, phone_number, alarm_history)

                if sockfd in read:
                    process_sock_request(sockfd)

    return 0


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

    check_running_root()
    log_fd = init_logging()

    if args.create_config:
        write_config_exit(args.config_path)

    if args.notification_test:
        notification_test_exit()

    initialize(args.config_path)

    context = daemon.DaemonContext(
        files_preserve=[log_fd],
        detach_process=(
            not args.no_fork),
        pidfile=lockfile.FileLock('/var/run/alarmd.pid'),
        stderr=(
            stderr if args.no_fork else None),
        stdout=(
            stdout if args.no_fork else None))
    context.signal_map = {signal.SIGTERM: sigcleanup_handler,
                          signal.SIGINT: sigcleanup_handler}

    with context:
        logging.info(
            "Starting in %s mode",
            'no-fork' if args.no_fork else 'daemonized')
        alarm_main_loop()


if __name__ == "__main__":
    sys.exit(main())
