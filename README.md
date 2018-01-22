# alarm-central-station-receiver
  
## Disclaimer 
I make no warranties or guarantees on the relability of this software when it comes to monitoring your home alarm system.  It's simply intended to be a fun software project!

## Overview
So what is this?  This is a python-based project for receiving Contact-ID messages from a home alarm system.  It listens for incoming phone calls via a USB magicJack (the original silver kind), decodes the DTMF codes from the alarm, and relays the messages to the user via e-mail.  Only a magicJack is supported, though any USB device that can decode DTMF and detect on-hook/off-hook could work with this software.

<p align="center"><img src=documentation/alarm-diagram.jpg /></p>
          
### Can you explain in more detail?

The alarm-central-station-receiver daemon relies on the magicJack to signal to it when the home alarm system is dialing out.  When this occurs, the daemon answers the phone, and responds to the alarm with the contact-id handshake.  Credit to li0r for [explaining the protocol](https://li0r.wordpress.com/contact-id-protocol/)

Once the alarm receives the contact-id handshake it begins transmitting its messages to the daemon via DTMF codes.  These codes are decoded by the magicJack hardware, and read into the daemon as integers via a hidraw0 interface.  Once the alarm completes transmitting its messages the daemon relays them to the configured e-mail address.  If you use your phone provider's email to SMS bridge you can receive the notifications via SMS.  For example for T-Mobile it's [yournumber]@tmomail.net

Since the software is decoding contact-id messages from the alarm, these are at the same level of detail that an alarm company would receive.  The full list of codes can be [found here](https://github.com/scudre/alarm-central-station-receiver/blob/master/alarm_central_station_receiver/contact_id/dsc.py).

### What inspired you to build this?

I wanted to be able to monitor my alarm system without having to pay a monthly fee to an alarm company.  I came across many implementations that allow you to monitor your DSC Powerseries alarm systems.  For these systems there is an easy-to-use serial communciation channel.  Unfortunately, my alarm, the DSC Alexor PC9155, does not support communciation via serial.  

Digging around online, I came across li0r's [Alarmino project](https://li0r.wordpress.com/) which inspired me to also go the route of communciating with the alarm via telephone and the contact-id protocol.  Instead of building hardware to emulate a telephone, I opted to go the route of using a USB magicJack + Rasberry Pi + daemon written in python.

## Setup
### Required Hardware & Software

1) Debian OS — Should work with any Linux distro, but only this one has been tested
2) Original silver USB magicJack — You can find this on eBay for pretty cheap
3) Alarm System — See 'Alarm Systems' below
4) (Optional) Raspberry Pi — This is great to use as you can mount it in a small box right next to your alarm system

#### Alarm Systems
This software communciates with the alarm via telephone and the Contact-ID protocol, which is supported by just about every alarm system out there.  So this will most likely work with yours.  At this time, the software has only been confirmed to work with one system:

- DSC Alexor PC9155

## Acknowledgments
* Thanks to li0r for explaining the contact ID protocol, and providing the inspiration for my project: https://li0r.wordpress.com
* Thanks to Môshe van der Sterre for writing the original TigerJet driver: http://moshe.nl/tjapi.html
