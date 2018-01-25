import glob
import pytjapi

TJ_ID = ''


def hidraw_path():
    return '/dev/hidraw%s' % TJ_ID


def initialize():
    """
    Initialize the TigerJet 560B USB device for use with the alarm.
    This involves enabling the DTMF HID reports, and lowering the
    DTMF decoder threshold.  For some reason the default threshold
    is unable to detect the DTMF tones sent by the alarm.

    :raises ValueError: if TigerJet not found
    """
    for file_name in glob.glob('/dev/usb/hiddev*'):
        with open(file_name, 'rb') as fd:
            if not pytjapi.is_tigerjet(fd.fileno()):
                continue

            # Enable DTMF and Hook Status HID reports
            data = pytjapi.read(fd.fileno(), 0x4e)
            pytjapi.write(fd.fileno(), 0x4e, (data | 0x40))

            # Lower the DTMF decoder threshold from 0x199 to 0x50
            # This is required to work with the DSC PC9155 alarm
            pytjapi.write(fd.fileno(), 0x35, 0x50)
            pytjapi.write(fd.fileno(), 0x36, 0)

            global TJ_ID
            TJ_ID = file_name[15:]
            break
    else:
        raise ValueError('Unable to find TigerJet Device')
