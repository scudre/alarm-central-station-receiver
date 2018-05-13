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
import logging
import wave
import time
import os.path
from pyaudio import PyAudio, paContinue

TJ_DEV_INDEX = -1


class Handshake(object):
    def __init__(self):
        self.wf = ''
        self.stream = ''
        self.p = ''

    def __enter__(self):
        """
        Initiate a contact id handshake with the alarm that has called the Rpi.

        :returns: tuple of the PyAudio, wave file, and stream objects.  For passing
                  into cleanup_alarm_handshake()
        """
        logging.info("Handshake Initiated")

        # TigerJet seems to only support 8k & 16k sample rates
        self.wf = wave.open(
            os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    'handshake16k.wav')),
            'rb')

        self.p = PyAudio()

        def play_alarm(in_data, frame_count, time_info, status):
            data = self.wf.readframes(frame_count)
            return (data, paContinue)

        self.stream = self.p.open(
            format=self.p.get_format_from_width(
                self.wf.getsampwidth()),
            channels=self.wf.getnchannels(),
            rate=self.wf.getframerate(),
            output=True,
            stream_callback=play_alarm,
            output_device_index=TJ_DEV_INDEX)

        self.stream.start_stream()

    def __exit__(self, exc_type, exc_value, traceback):
        while self.stream.is_active():
            time.sleep(0.3)

        self.stream.stop_stream()
        self.stream.close()
        self.wf.close()

        self.p.terminate()
        logging.info("Handshake Complete")


def find_tigerjet_audio_device():
    p = PyAudio()
    for dev_idx in range(0, p.get_device_count()):
        if 'TigerJet' in p.get_device_info_by_index(dev_idx).get('name'):
            global TJ_DEV_INDEX
            TJ_DEV_INDEX = dev_idx
            break
    else:
        raise RuntimeError('TigerJet audio output device not found!')


def initialize():
    find_tigerjet_audio_device()
