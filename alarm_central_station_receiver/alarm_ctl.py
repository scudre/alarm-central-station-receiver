#!/usr/bin/env python
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
import argparse
from os import geteuid
import sys

from json_ipc import send_client_msg


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

    parser.add_argument('command', choices=['arm', 'disarm', 'auto-arm', 'auto-disarm'],
                        help=help_text)

    args = parser.parse_args()
    check_running_root()

    error_msg = send_client_msg({'command': args.command})
    if not error_msg:
        sys.stdout.write('Success')
        return 0

    sys.stderr.write('Error: %s', error_msg)
    return -1


if __name__ == "__main__":
    sys.exit(main())
