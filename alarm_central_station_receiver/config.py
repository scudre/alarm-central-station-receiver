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

CONFIG_MAP = {
    'Main': {
        'required': True,
        'keys': {
            'phone_number': True,
            'data_file_path': True,

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

        for sec_name, section in CONFIG_MAP.iteritems():
            optional = not section.get('required')
            missing = not config.get(sec_name)

            # If an entire section is missing, and its an optional
            # section, skip validation.
            if optional and missing:
                continue

            for key, key_required in section.get('keys', {}).iteritems():
                cfg_value = config.get(sec_name, {}).get(key, '')

                if key_required and cfg_value == '':
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
