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
from alarm_central_station_receiver.contact_id import handshake


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
                off_hook, digit = get_phone_status(fd)
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

    # XXX hack - Tigerjet can't detect the highest DTMF code of 14
    if len(code) == 15 and checksum % 15 == 1:
        code += format(14, 'x')
        codes.append((False, code))
        code = ''
        checksum = 0

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

    # XXX for python 3 no need to have ORD, can directly read/write
    # values as they are already in bytes
    status = fd.read(2)

    off_hook = ((ord(status[1]) & 0x80) == 0x80)
    digit = ord(status[0])

    if digit < 11:
        digit = digit - 1

    return (off_hook, digit)


def handle_alarm_calling(fd, number):
    codes = []
    if validate_alarm_call_in(fd, number):
        codes = collect_alarm_codes(fd)

    return codes
