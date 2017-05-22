import ctypes

def initialize():
    """
    Initialize the TigerJet 560B USB device for use with the alarm.
    This involves enabling the DTMF HID reports, and lowering the
    DTMF decoder threshold.  For some reason the default threshold
    is unable to detect the DTMF tones sent by the alarm.

    :raises assert: if any of the calls fail
    """
    with open('/dev/usb/hiddev0', 'rb') as fd:
        tjapi = ctypes.CDLL("libtjapi.so")

        # Enable DTMF and Hook Status HID reports
        data = ctypes.c_ubyte(0)
        ret = tjapi.read_tigerjet(fd.fileno(),
                                  ctypes.c_ubyte(0x4e),
                                  ctypes.pointer(data))
        assert ret == 0

        ret = tjapi.write_tigerjet(fd.fileno(),
                                   ctypes.c_ubyte(0x4e),
                                   ctypes.c_ubyte(data.value | 0x40))
        assert ret == 0

        # Lower the DTMF decoder threshold from 0x199 to 0x50
        # This is required to work with the DSC PC9155 alarm
        ret = tjapi.write_tigerjet(fd.fileno(),
                                   ctypes.c_ubyte(0x35),
                                   ctypes.c_ubyte(0x50))
        assert ret == 0
        
        ret = tjapi.write_tigerjet(fd.fileno(),
                                   ctypes.c_ubyte(0x36),
                                   ctypes.c_ubyte(0x0))
        assert ret == 0
