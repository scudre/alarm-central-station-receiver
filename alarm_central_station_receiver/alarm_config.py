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
import ConfigParser
import shutil
import os.path

LOADED_CONFIG = {}


class AlarmConfig:
    @staticmethod
    def exists(path):
        return os.path.isfile(path)

    @staticmethod
    def load(path):
        config = ConfigParser.ConfigParser()
        config.read(path)
        global LOADED_CONFIG
        LOADED_CONFIG = {key: dict(config.items(key))
                         for key in config.sections()}

    @staticmethod
    def get(*argv):
        config = LOADED_CONFIG
        for arg in argv:
            config = config.get(arg, {})

        return config

    @staticmethod
    def validate(config):
        missing_config = []
        if not config.get('AlarmSystem', {}).get('phone_number'):
            missing_config.append('[AlarmSystem] Section: phone_number')

        email_keywords = ['username',
                          'password',
                          'server_address',
                          'port',
                          'notification_email',
                          'notification_subject',
			  'tls']

        for keyword in email_keywords:
            if not config.get('EmailNotification', {}).get(keyword):
                missing_config.append('[EmailNotification] Section: %s' % keyword)

        return missing_config

    @staticmethod
    def create(path):
        if not AlarmConfig.exists(path):
            shutil.copy(
                os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        'config_template.ini')),
                path)
            return True

        return False
