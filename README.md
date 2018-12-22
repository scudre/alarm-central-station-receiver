# alarm-central-station-receiver
  
## Disclaimer 
I make no warranties or guarantees on the relability of this software when it comes to monitoring your home alarm system.  It's simply intended to be a fun software project!

## Overview
So what is this?  This is a python-based project for receiving Contact-ID messages from a home alarm system.  It listens for incoming phone calls via a USB magicJack (the original silver kind), decodes the DTMF codes from the alarm, and relays the messages to the user via e-mail or [Pushover](http://www.pushover.net).  Only a magicJack is supported, though any USB device that can decode DTMF and detect on-hook/off-hook could work with this software.

<p align="center"><img src=documentation/alarm-diagram.jpg /></p>
          
### Can you explain in more detail?

The alarm-central-station-receiver daemon relies on the magicJack to signal to it when the home alarm system is dialing out.  When this occurs, the daemon answers the phone, and responds to the alarm with the contact-id handshake.  Credit to li0r for [explaining the protocol](https://li0r.wordpress.com/contact-id-protocol/)

Once the alarm receives the contact-id handshake it begins transmitting its messages to the daemon via DTMF codes.  These codes are decoded by the magicJack hardware, and read into the daemon as integers via a hidraw0 interface.  Once the alarm completes transmitting its messages the daemon relays them to the configured e-mail address (or Pushover).  If you use your phone provider's email to SMS bridge you can receive the notifications via SMS.  For example for T-Mobile it's [yournumber]@tmomail.net

Since the software is decoding contact-id messages from the alarm, these are at the same level of detail that an alarm company would receive.  The full list of codes can be [found here](https://github.com/scudre/alarm-central-station-receiver/blob/master/alarm_central_station_receiver/contact_id/dsc.py).

### What inspired you to build this?

I wanted to be able to monitor my alarm system without having to pay a monthly fee to an alarm company.  I came across many implementations that allow you to monitor your DSC Powerseries alarm systems.  For these systems there is an easy-to-use serial communciation channel.  Unfortunately, my alarm, the DSC Alexor PC9155, does not support communciation via serial.  

Digging around online, I came across li0r's [Alarmino project](https://li0r.wordpress.com/) which inspired me to also go the route of communciating with the alarm via telephone and the contact-id protocol.  Instead of building hardware to emulate a telephone, I opted to go the route of using a USB magicJack + Rasberry Pi + daemon written in python.

## Setup
### 1. Required Hardware & Software

1. Debian OS — Should work with any Linux distro, but only this one has been tested
1. Original silver USB magicJack — You can find this on eBay for pretty cheap
1. Alarm System — See 'Alarm Systems' below
1. (Optional) Raspberry Pi — This is great to use as you can mount it in a small box right next to your alarm system

#### Alarm Systems
This software communciates with the alarm via telephone and the Contact-ID protocol, which is supported by just about every alarm system out there.  So this will most likely work with yours.  At this time, the software has only been confirmed to work with one system:

- DSC Alexor PC9155

### 2. Installation

##### 1. Clone the repository

```
git clone https://github.com/scudre/alarm-central-station-receiver.git
```

##### 2. Install using your favorite python installation method

e.g.

```
python setup.py install
```

or

```
pip install <path/to/project>
```

This will install three console scripts:

* **alarmd** - This is main daemon that monitors your alarm system via MagicJack, and sends out notifications.
* **alarmd-webui** - This is an optional dameon which hosts a basic REST API for arming, disarm, gett system status, and getting event history
* **alarm-ctl** - This is a command line script for arming, disarm, gett system status, and getting event history

##### 3. Create configuration file for alarm daemon

The alarmd daemon requires a configuration file, and a few settings set to run.  You need to run alarmd as root to create the configuration file:

```
sudo alarmd --create-config
```

By default it will create the configuration in `/etc/alarmd_config.ini`.  A non-default path can be used by also including `-c <path/filename>`.

##### 3. Edit configuration file for alarm daemon

[See the template file](https://github.com/scudre/alarm-central-station-receiver/blob/master/alarm_central_station_receiver/config_template.ini) for reference on what's generated with the `create--config` command.

The only required configuration is under the `[Main]` header, specifically `phone_number`.  However, at minimum you should configure either email notifications or [Pushover](http://www.pushover.net).  Otherwise the only notification for alarm events would be in `/var/log/alarmd.log`.

###### 3a. Set the phone number your alarm system "calls"

alarmd needs to know the phone number that the alarm system is "calling" so that it knows to answer the phone and initiate the contact-id handshake.  

For the PC9155, this usually is the phone number set in `[301]` section of the programming mode.  You can enter it by doing `[*][8][<installer code>][301]`.  See section 5.3 of your PC9155 DSC installation manual for more info.

##### 4. Start alarmd the first time!

Since alarmd needs to read the MagicJack files in `/dev` it needs to be run as root.  By default when starting alarmd, it will automatically daemonize.  Since this is the first time we're starting it, we'll run it in the foreground:

```
sudo alarmd --no-fork
```

If you decided to put your alarmd configuration in a different location than `/etc/alarmd_config.ini` you'll need to also include the `-c <path/filename>`

##### 4. Verify it's running okay

When you start the daemon, there may be a flood of error messages from the sound library, these are generated when alarmd initializes pyaudio, and can be safely ignored: 

```
ALSA lib confmisc.c:1286:(snd_func_refer) Unable to find definition 'cards.bcm2835.pcm.front.0:CARD=0'
<additional ALSA LIB messages>
Cannot connect to server socket err = No such file or directory
Cannot connect to server request channel
jack server is not running or cannot be started
```

If everything loaded up properly, including the daemon being able to find the MagicJack USB device you'll see the following messages:

```
Sep 11 18 12:11:41 AM alarmd[32667]: [main.INFO] Python 3.4.2 (default, Oct 19 2014, 13:31:11) [GCC 4.9.1]
Sep 11 18 12:11:41 AM alarmd[32667]: [main.INFO] Starting in no-fork mode
Sep 11 18 12:11:41 AM alarmd[32667]: [status.INFO] Loading config from /var/alarmd_db
Sep 11 18 12:11:41 AM alarmd[32667]: [main.INFO] Ready, listening for alarms
```

As a sanity check you can query the status via the `alarm-ctl status` command.  If everything is loaded smoothly it will return the initial system status:

```
me@myhost:~$ sudo alarm-ctl status
Auto Arm: False
Arm Status Time: 0
System Status: Ok
Arm Status: Disarmed
```

##### 5. Trigger your alarm system to call alarmd

The easiest, albeit loudest way to send an event is to trigger your alarm system to go off.  Though for most systems, including the PC9155, an event is triggered when entering and exiting the installer programming mode.  This can be done via `[*][8][<installer code>]`.  If everything went right you'll see the following messages in your terminal:

```
Aug 17 18 09:22:03 AM alarmd[440]: [callup.INFO] Phone Off The Hook
Aug 17 18 09:22:11 AM alarmd[440]: [callup.INFO] Alarm Call In Received
Aug 17 18 09:22:11 AM alarmd[440]: [callup.INFO] Collecting Alarm Codes
Aug 17 18 09:22:11 AM alarmd[440]: [handshake.INFO] Handshake Initiated
Aug 17 18 09:22:18 AM alarmd[440]: [callup.INFO] Alarm Hung Up
Aug 17 18 09:22:29 AM alarmd[440]: [handshake.INFO] Handshake Complete
Aug 17 18 09:22:29 AM alarmd[440]: [status.INFO] New Events
Aug 17 18 09:22:29 AM alarmd[440]: [status.INFO] MA: Installer Lead In, MA: Installer Lead Out
Aug 17 18 09:22:29 AM alarmd[440]: [status.INFO] Saving config to /var/alarmd_db
Aug 17 18 09:22:29 AM alarmd[3987]: [notify.INFO] Sending notifications...
```

## Console Scripts

### alarmd

### alarmd-webui

### alarm-ctl

## Troubleshooting

## FAQ


## Acknowledgments
* Thanks to li0r for explaining the contact ID protocol, and providing the inspiration for my project: https://li0r.wordpress.com
* Thanks to Môshe van der Sterre for writing the original TigerJet driver: http://moshe.nl/tjapi.html
