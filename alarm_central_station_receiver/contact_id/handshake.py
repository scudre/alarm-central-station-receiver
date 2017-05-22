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

class Handshake():
    def __enter__(self):
        """
        Initiate a contact id handshake with the alarm that has called the Rpi.

        :returns: tuple of the PyAudio, wave file, and stream objects.  For passing
                  into cleanup_alarm_handshake()
        """
        logging.info("Handshake Initiated")

        self.wf = wave.open(
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'handshake.wav')),
            'rb')

        self.p = PyAudio()

        def play_alarm(in_data, frame_count, time_info, status):
            data = self.wf.readframes(frame_count)
            return (data, paContinue)

        self.stream = self.p.open(format=self.p.get_format_from_width(self.wf.getsampwidth()),
                                  channels=self.wf.getnchannels(),
                                  rate=self.wf.getframerate(),
                                  output=True,
                                  stream_callback=play_alarm)

        self.stream.start_stream()

    def __exit__(self, exc_type, exc_value, traceback):
        while self.stream.is_active():
            time.sleep(0.3)

        self.stream.stop_stream()
        self.stream.close()
        self.wf.close()

        self.p.terminate()
        logging.info("Handshake Complete")
