#!/usr/bin/env python
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
import argparse
from os import geteuid
import sys

from alarm_central_station_receiver.json_ipc import send_client_msg


def check_running_root():
    if geteuid() != 0:
        sys.stderr.write("Error: Alarmd must run as root - exiting\n")
        sys.exit(-1)


def main():
    parser = argparse.ArgumentParser(
        prog='alarm-ctl', formatter_class=argparse.RawTextHelpFormatter)
    help_text = """Arm or disarm the alarm system

The auto-disarm command only disarms, if auto-arm was used to arm.
This is useful if you want to have a cron job automatically arm/disrm 
the system daily, but want to skip disarming if the system was armed
on the keypad, or with the regular arm command.
"""

    parser.add_argument('command', choices=['arm', 'disarm', 'auto-arm', 'auto-disarm', 'status', 'history'],
                        help=help_text)
    parser.add_argument('--start-index', type=int)
    parser.add_argument('--end-index', type=int)

    args = parser.parse_args()
    check_running_root()

    request_msg = {'command': args.command}

    if args.command == 'history':
        if not args.start_idx or not args.end_index:
            sys.stderr.write(
                'Error: start-index and end-index required with history command')
            return -1

        options = {'start_idx': args.start_index,
                   'end_idx': args.end_index
                   }
        request_msg['options'] = options

    rsp, serr = send_client_msg(request_msg)
    if serr:
        sys.stderr.write('%s\n' % serr)
        return -1

    error_msg = rsp.pop('error')
    if error_msg:
        sys.stderr.write('Error: %s\n' % error_msg)
        return -1

    if args.command == 'status':
        for key, value in rsp.get('response').items():
            sys.stdout.write('%s: %s\n' %
                             (key.replace('_', ' ').title(), value.title()))
    else:
        sys.stdout.write('%s\n' % rsp.get('response'))

    return 0


if __name__ == "__main__":
    sys.exit(main())
