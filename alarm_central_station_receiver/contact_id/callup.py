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
import re
from alarm_central_station_receiver.contact_id import handshake


def calc_checksum(code):
    checksum = 0
    for digit in code:
        # 0 is treated as 10 in the checksum calculation
        checksum += int(digit, 16) if digit != '0' else 10

    return checksum % 15


def parse_alarm_codes(code_str):
    pattern = "([0-9]{4}18[136][0-9abcdef]{8}[0-9abcdef]?(?![0-9]{3}18[136]))"
    codes = []
    for code in re.split(pattern, code_str):
        if not code:
            continue

        # There seems to be some buggyness with either TigerJet or the alarm system
        # when sending the last checksum digit when its above 'c'
        if len(code) == 15:
            # XXX hack - Tigerjet can't detect the highest DTMF code of 15
            if calc_checksum(code) == 0:
                code += 'f'

            # XXX hack - Tigerjet can't detect the high DTMF code of 14
            if calc_checksum(code) == 1:
                code += 'e'

            if calc_checksum(code) == 2:
                code += 'd'

        codes.append((code, calc_checksum(code) == 0))

    return codes


def collect_alarm_codes(fd):
    logging.info("Collecting Alarm Codes")
    code_str = ''

    # Play the alarm handshake to start getting the codes
    with handshake.Handshake():
        off_hook, digit = get_phone_status(fd)
        while off_hook:
            code_str += format(digit, 'x') if digit != -1 else ''
            off_hook, digit = get_phone_status(fd)

        logging.info("Alarm Hung Up")

    logging.info('Code String: %s', code_str)
    return code_str


def validate_alarm_call_in(fd, expected):
    number = '000'
    off_hook, digit = get_phone_status(fd)

    if off_hook:
        logging.info("Phone Off The Hook")

    while off_hook:
        if digit != -1:
            logging.debug("Digit %d", digit)
            number = number[1:] + format(digit, 'x')
            logging.debug("Number %s", number)

        if number == expected:
            logging.info("Alarm Call In Received")
            break

        off_hook, digit = get_phone_status(fd)
    logging.debug("Number %s", number)

    if not off_hook:
        logging.info("Phone On The Hook")

    return number == expected and off_hook


def get_phone_status(fd):
    status = bytearray(fd.read(2))
    digit = status[0]
    if digit < 11:
        digit = digit - 1

    off_hook = ((status[1] & 0x80) == 0x80)

    return (off_hook, digit)


def handle_alarm_calling(fd, number):
    codes = []
    if validate_alarm_call_in(fd, number):
        code_str = collect_alarm_codes(fd)
        codes = parse_alarm_codes(code_str)

    return codes
