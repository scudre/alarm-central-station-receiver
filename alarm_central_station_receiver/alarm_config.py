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
        LOADED_CONFIG = { key : dict( config.items(key) ) for key in config.sections() }

    @staticmethod
    def get(*argv):
        config = LOADED_CONFIG
        for arg in argv:
            config = config.get(arg, {})

        return config

    @staticmethod
    def validate(config):
        missing_config = []
        if not config.get('AlarmSystem').get('phone_number'):
            missing_config.append('[AlarmSystem] Section: phone_number')

        email_keywords = ['username',
                          'password',
                          'server_address',
                          'port',
                          'notification_email']

        email_config = config.get('EmailNotification')
        for keyword in email_keywords:
            if not email_config.get(keyword):
                missing_config.append('[EmailNotification] Section: %s' % keyword)

        return missing_config

    @staticmethod
    def create(path):
        if not AlarmConfig.exists(path):
            shutil.copy(os.path.abspath(
                os.path.join(os.path.dirname(__file__), 'config_template.ini')),
                path)
            return True

        return False
