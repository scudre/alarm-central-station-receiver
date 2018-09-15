import sys
from distutils.version import StrictVersion
from setuptools import setup, find_packages, Extension, __version__

if StrictVersion(__version__) < StrictVersion('20.2'):
    print('Your setuptools version is too old and does not support '
          'PEP 508. Please upgrade setuptools to 20.2+ and repeat the '
          'installation.')
    sys.exit(1)

pytjapi = Extension(
    'pytjapi',
    sources=['alarm_central_station_receiver/tigerjet/pytjapi.c']
)

setup(
    name='alarm_central_station_receiver',
    version='1.0.0',
    author='Chris Scuderi',
    license='Apache License Version 2.0',
    description='Software based central station receiver for home alarm systems',
    packages=find_packages(),
    ext_modules=[pytjapi],
    zip_safe=False,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'alarmd=alarm_central_station_receiver.main:main',
            'alarm-ctl=alarm_central_station_receiver.alarm_ctl:main',
            'alarmd-webui=alarm_central_station_receiver.webui:main'
        ]
    },

    install_requires=[
        'pyaudio',
        'python-daemon-3k',
        'requests',
        'configparser;python_version<"3"',
    ],
    extras_require={
        'RPI': ['RPi.GPIO'],
        'webui': 'flask'
    }
)
