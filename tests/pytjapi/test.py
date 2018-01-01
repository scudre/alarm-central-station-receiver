import os
from ctypes import *
import pytjapi

tjapi = CDLL("libtjapi2.so")

fd = os.open('/dev/usb/hiddev0', os.O_RDWR)
print "Is TigerJet?: %d" % tjapi.is_tigerjet(c_int(fd), None)
print "Is TigerJet?: "
print pytjapi.is_tigerjet(fd)

addr = c_ubyte(0x4e)
data = c_ubyte(0x40)

print "Old Library"
print "=================="
print "Calling Write:"
print tjapi.write_tigerjet(fd, addr, data)

print "Calling Read:"
data = c_ubyte(0)
print tjapi.read_tigerjet(fd, addr, pointer(data))

print "Value: "
print hex(data.value)

print
print "New Wrapper"
print "==================="
print "Calling New Write:"
addr = 0x4e
data = 0x40
print pytjapi.write(fd, addr, data)

print "Calling New Read:"

print "Value: "
print hex(pytjapi.read(fd, addr))

print "Calling Old Read:"
data = c_ubyte(0)
print tjapi.read_tigerjet(fd, addr, pointer(data))

print "Value: "
print hex(data.value)



