"""
DSC Contact ID Codes to Descriptions
"""
from alarm_central_station_receiver.config import AlarmConfig

EVENTS = {
    '100000': {'1': ('A', 'Aux Key Alarm')},
    '100ZZZ': {'1': ('A', '24 Hr Medical')},
    '101ZZZ': {'1': ('A', '24 Hr Emergency (non-medical)')},
    '102000': {'1': ('A', 'Fail to Report In')},
    '110000': {'1': ('A', '[F] Key Alarm')},
    '110ZZZ': {'1': ('A', '24 Hr Fire')},
    '120000': {'1': ('A', 'Panic Key Alarm')},
    '120ZZZ': {'1': ('A', '24 Hr Panic')},
    '121000': {'1': ('A', 'Duress Alarm')},
    '130ZZZ': {'1': ('A', 'Zone Alarm')},
    '139000': {'1': ('A', 'Cross Zone Alarm')},
    '140ZZZ': {'1': ('A', '24 Hr Supervisory Buzzer')},
    '145000': {'1': ('T', 'General System Tamper (Case/Cover Tamper Alarm)')},
    '150ZZZ': {'1': ('A', '24 Hr Supervisory')},
    '151ZZZ': {'1': ('A', '24 Hr Gas')},
    '154ZZZ': {'1': ('A', '24 Hr Water')},
    '159ZZZ': {'1': ('A', '24 Hr Freeze')},
    '162ZZZ': {'1': ('A', '24 Hr CO Alarm')},
    '300000': {'1': ('MA', 'General System Trouble')},
    '300001': {'1': ('MA', 'General Alternate Communicator Trouble')},
    '301000': {'1': ('MA', 'AC Line Trouble')},
    '302000': {'1': ('MA', 'Battery Trouble')},
    '312000': {'1': ('MA', 'Auxiliary Power Trouble')},
    '330000': {'1': ('MA', 'Alternate Communicator Fault')},
    '350001': {'1': ('MA', 'Alternate Communicator Receiver 1 Trouble')},
    '350002': {'1': ('MA', 'Alternate Communicator Receiver 2 Trouble')},
    '350003': {'1': ('MA', 'Alternate Communicator Receiver 3 Trouble')},
    '350004': {'1': ('MA', 'Alternate Communicator Receiver 4 Trouble')},
    '351000': {'1': ('MA', 'Phone Line Failure')},
    '354000': {'1': ('MA', 'Phone #1-4 FTC')},
    '373000': {'1': ('MA', 'Fire Trouble')},
    '374ZZZ': {'1': ('C', 'Exit Fault')},
    '378000': {'1': ('A', 'Burglary Not Verified')},
    '380070': {'1': ('MA', 'Keypad 1 Fault')},
    '380071': {'1': ('MA', 'Keypad 2 Fault')},
    '380072': {'1': ('MA', 'Keypad 3 Fault')},
    '380073': {'1': ('MA', 'Keypad 4 Fault')},
    '380080': {'1': ('MA', 'Siren 1 Fault')},
    '380081': {'1': ('MA', 'Siren 2 Fault')},
    '380082': {'1': ('MA', 'Siren 3 Fault')},
    '380083': {'1': ('MA', 'Siren 4 Fault')},
    '380ZZZ': {'1': ('MA', 'Zone Fault')},
    '383070': {'1': ('T', 'Keypad 1 Tamper')},
    '383071': {'1': ('T', 'Keypad 2 Tamper')},
    '383072': {'1': ('T', 'Keypad 3 Tamper')},
    '383073': {'1': ('T', 'Keypad 4 Tamper')},
    '383080': {'1': ('T', 'Siren 1 Tamper')},
    '383081': {'1': ('T', 'Siren 2 Tamper')},
    '383082': {'1': ('T', 'Siren 3 Tamper')},
    '383083': {'1': ('T', 'Siren 4 Tamper')},
    '383ZZZ': {'1': ('T', 'Zone Tamper')},
    '384000': {'1': ('MA', 'Wireless Device Low Battery Trouble')},
    '384ZZZ': {'1': ('MA', 'Wireless Zone Low Battery Trouble')},
    '400000': {'1': ('O', 'Special Disarming'),
               '3': ('C', 'Special Arming')},
    '401UUU': {'1': ('O', 'System Disarmed'),
               '3': ('C', 'System Armed')},
    '406UUU': {'1': ('A', 'Alarm Cleared')},
    '411000': {'1': ('MA', 'DLS Lead In')},
    '412000': {'1': ('MA', 'DLS Lead Out')},
    '453000': {'1': ('O', 'Late to Open')},
    '456000': {'1': ('C', 'Partial Arming')},
    '458000': {'1': ('E', 'Disarm After Alarm')},
    '459UUU': {'1': ('A', 'Alarm Within 2 min of Arming')},
    '461000': {'1': ('T', 'Keypad Lockout')},
    '570ZZZ': {'1': ('C', 'Zone Bypass')},
    '601000': {'1': ('E', 'System Test')},
    '602000': {'1': ('E', 'Periodic Test')},
    '607UUU': {'1': ('E', 'Walk Test Begin'),
               '3': ('R', 'Walk Test End')},
    '627000': {'1': ('MA', 'Installer Lead In')},
    '628000': {'1': ('MA', 'Installer Lead Out')},
    '654000': {'1': ('MA', 'Delinquency')}
}


def create_event_description(event_type, event):
    """
    Create the alarm description by using the '1' event type
    description and appending the appropriate event type
    name to it for the passed in `event_type`
    """
    _, description = event.get('1')
    if event_type == '1':
        event_type_name = 'E'
    elif event_type == '3':
        event_type_name = 'R'
        description += ' Restoral'
    elif event_type == '6':
        event_type_name = 'S'
        description += ' Status'
    else:
        event_type_name = 'U'
        description += 'Unknown Event Type (%s)' % event_type

    return event_type_name, description


def get_zone_name(sensor_code):
    zone_name = AlarmConfig.config.get('ZoneMapping',
                                       sensor_code,
                                       fallback=None)
    if not zone_name:
        zone_name = 'Zone %s' % sensor_code

    return zone_name


def digits_to_alarmreport(code):
    """
    Given a raw contact id DTMF string from a DSC alarm,
    return the alarm description and event type.

    4567 18 1 570 00 016 4
    ACCT MT Q CCC GG ZZZ S
    NNNN 18 1 = new event
            3 = restore or closing
            6 = still present (status report)
    """
    event_type = code[6]
    event_code = code[7:10]
    sensor_code = code[12:15]

    event_type_name = 'U'
    description = 'Unknown Event - %s' % code
    extra_desc = ''

    event = EVENTS.get(event_code + sensor_code)
    if not event:
        zone_event = EVENTS.get(event_code + 'ZZZ')
        user_event = EVENTS.get(event_code + 'UUU')
        if zone_event:
            event = zone_event
            zone_name = get_zone_name(sensor_code)
            extra_desc = ' %s (%s)' % (zone_name, sensor_code)
        elif user_event:
            event = user_event
            extra_desc = ' User %s' % sensor_code

    if event:
        if event_type in event:
            event_type_name, description = event.get(event_type)
        else:
            event_type_name, description = \
                create_event_description(event_type, event)

        description += extra_desc

    return event_type_name, event_code + sensor_code, description
