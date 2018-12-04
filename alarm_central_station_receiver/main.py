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

from os import geteuid
from select import select

from alarm_central_station_receiver import tigerjet
from alarm_central_station_receiver import json_ipc
from alarm_central_station_receiver.contact_id import handshake, decoder, callup
from alarm_central_station_receiver.status import AlarmStatus
from alarm_central_station_receiver.system import AlarmSystem
from alarm_central_station_receiver.config import AlarmConfig
from alarm_central_station_receiver.notifications import notify, notify_test


def init_logging(stdout_only, debug_logs):
    root_logger = logging.getLogger('')
    log_level = logging.DEBUG if debug_logs else logging.INFO
    root_logger.setLevel(log_level)
    formatter = logging.Formatter(
        fmt='%(asctime)s alarmd[%(process)d]: [%(module)s.%(levelname)s] %(message)s',
        datefmt='%b %d %y %I:%M:%S %p')

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    log_fd = None
    if not stdout_only:
        log_file = logging.FileHandler('/var/log/alarmd.log')
        log_file.setLevel(log_level)
        log_file.setFormatter(formatter)
        root_logger.addHandler(log_file)
        log_fd = log_file.stream

    return log_fd


def sigcleanup_handler(signum, _):
    sig_name = next(v for v, k in signal.__dict__.items() if k == signum)
    logging.info("Received %s, exiting", sig_name)
    sys.exit(0)


def check_running_root():
    if geteuid() != 0:
        sys.stderr.write("Error: Alarmd must run as root - exiting\n")
        sys.exit(-1)


def create_or_check_required_config(path):
    if not AlarmConfig.exists(path):
        logging.info('Configuration missing, writing to %s.\n\n', path)
        AlarmConfig.create(path)

    AlarmConfig.load(path)
    missing_config = AlarmConfig.validate()
    if missing_config:
        logging.error(
            'The following required configuration is missing from %s\n\n',
            path)
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
            'Configuration at %s already exists, skipping write\n',
            config_path)

    sys.exit(0)


def notification_test_exit(config_path):
    logging.info('Notification test starting...')
    create_or_check_required_config(config_path)
    notify_test()
    logging.info('Notification test complete, exiting.')
    sys.exit(0)


def process_alarm_timeout(alarm_system):
    logging.info('Arm/Disarm request timeout!')
    notify_events = alarm_system.abort_arm_disarm()
    notify(notify_events)


def process_alarm_event(alarmhid, phone_number, alarm_status):
    raw_events = callup.handle_alarm_calling(alarmhid, phone_number)
    events = decoder.decode(raw_events)
    notify_events = alarm_status.add_new_events(events)
    notify(notify_events)


def process_sock_request(sockfd, alarm_system):
    try:
        conn, _ = sockfd.accept()
        conn.settimeout(20)
        msg = json_ipc.recv(conn)
        command = msg.get('command')
        auto_arm = True if 'auto' in command else False
        if command in ['arm', 'auto-arm']:
            status = alarm_system.arm(auto_arm)
            rsp = {'error': False, 'response': status}
        elif command in ['disarm', 'auto-disarm']:
            status = alarm_system.disarm(auto_arm)
            rsp = {'error': False, 'response': status}
        elif command in ['status']:
            rsp = {
                'error': False,
                'response': {
                    'arm_status': alarm_system.alarm.arm_status,
                    'arm_status_time': alarm_system.alarm.arm_status_time,
                    'auto_arm': alarm_system.alarm.auto_arm,
                    'system_status': alarm_system.alarm.system_status
                }
            }
        elif command in ['history']:
            options = msg.get('options')
            offset = options.get('offset', 0)
            limit = options.get('limit', 1) + offset

            if offset < 0:
                rsp = {'error': 'Offset must be 0 or greater'}
            elif limit < 1:
                rsp = {'error': 'Limit must be 1 or greater'}
            else:
                rsp = {
                    'error': False,
                    'response': alarm_system.alarm.history[::-1][offset:limit]
                }
        else:
            rsp = {'error': 'Invalid command %s' % command}

        json_ipc.send(conn, rsp)
        conn.close()

    except socket.timeout:
        logging.error("Timed out receiving data from client")


def get_alarm_timeout(alarm_system):
    return 300 if alarm_system.alarm.arm_status in [
        'arming', 'disarming'] else None


def alarm_main_loop():
    phone_number = AlarmConfig.config.get('Main', 'phone_number')
    alarm_status = AlarmStatus()
    alarm_system = AlarmSystem()

    with open(tigerjet.hidraw_path(), 'rb') as alarmhid:
        with json_ipc.ServerSock() as sockfd:
            logging.info("Ready, listening for alarms")
            timeout = get_alarm_timeout(alarm_system)
            logging.debug('Timeout: %s', timeout)

            while True:
                read = []
                read, _, _ = select([alarmhid, sockfd], [], [], timeout)
                if alarmhid in read:
                    process_alarm_event(alarmhid, phone_number, alarm_status)

                if sockfd in read:
                    process_sock_request(sockfd, alarm_system)

                if not read:
                    # Arm/disarm event from alarm system never came
                    process_alarm_timeout(alarm_system)

                timeout = get_alarm_timeout(alarm_system)
                logging.debug('Timeout: %s', timeout)

    return 0


def main():
    parser = argparse.ArgumentParser(prog='alarmd')
    parser.add_argument(
        '--no-fork',
        action='store_true',
        default=False,
        help='Run alarmd in the foreground, useful for debugging')

    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='Log at debug level')

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
    log_fd = init_logging(args.no_fork, args.debug)

    if args.create_config:
        write_config_exit(args.config_path)

    if args.notification_test:
        notification_test_exit(args.config_path)

    initialize(args.config_path)

    context = daemon.DaemonContext(
        files_preserve=[log_fd],
        detach_process=(
            not args.no_fork),
        pidfile=lockfile.FileLock('/var/run/alarmd.pid'),
        stderr=(
            sys.stderr if args.no_fork else None),
        stdout=(
            sys.stdout if args.no_fork else None))
    context.signal_map = {signal.SIGTERM: sigcleanup_handler,
                          signal.SIGINT: sigcleanup_handler}

    with context:
        logging.info('Python %s', sys.version)
        logging.info(
            "Starting in %s mode",
            'no-fork' if args.no_fork else 'daemonized')
        alarm_main_loop()


if __name__ == "__main__":
    sys.exit(main())
