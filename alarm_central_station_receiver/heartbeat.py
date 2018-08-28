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
from alarm_central_station_receiver.config import AlarmConfig
import requests


def interval():
    if 'Heartbeat' not in AlarmConfig.config:
        return

    return AlarmConfig.config.get('Heartbeat', 'interval')


def beat():
    if 'Heartbeat' not in AlarmConfig.config:
        return

    url = AlarmConfig.config.get('Heartbeat', 'url')
    response = requests.get(url)

    if response.status_code == 200:
        logging.info('Heartbeat sent successfully')
    else:
        status_code = response.status_code
        error = response.json()
        logging.error('Unable to push heartbeat %s %s',
                      status_code, error)
