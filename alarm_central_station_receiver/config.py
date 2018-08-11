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
import configparser
import shutil
import os.path

CONFIG_MAP = {
    'Main': {
        'required': True,
        'keys': {
            'phone_number': True,
            'data_file_path': True,
            'notify_auto_events': True,
        }
    },

    'RpiArmDisarm': {
        'required': False,
        'keys': {'gpio_pin': True}
    },

    'ZoneMapping': {'required': False},
    'EmailNotification': {
        'required': False,
        'keys': {
            'username': True,
            'password': True,
            'server_address': True,
            'port': True,
            'notification_email': True,
            'notification_subject': True,
            'tls': True
        }
    },

    'PushoverNotification': {
        'required': False,
        'keys': {
            'user': True,
            'token': True,
            'priority': False,
            'device': False
        }
    },
}


class AlarmConfig(object):
    config = None

    @staticmethod
    def exists(path):
        return os.path.isfile(path)

    @classmethod
    def load(klass, path):
        klass.config = configparser.ConfigParser()
        klass.config.read(path)

    @classmethod
    def validate(klass):
        missing_config = []

        for sec_name, section in CONFIG_MAP.items():
            required = section.get('required')
            missing = sec_name not in klass.config

            # If an entire section is missing, and its an optional
            # section, skip validation.
            if missing and not required:
                continue

            for key, key_required in section.get('keys', {}).items():
                cfg_value = klass.config.get(sec_name, key, fallback=None)
                if key_required and not cfg_value:
                    missing_config.append('[%s] Section: %s' % (sec_name, key))

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
