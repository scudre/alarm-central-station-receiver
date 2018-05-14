from setuptools import setup, find_packages, Extension
from sys import version_info

pytjapi = Extension(
    'pytjapi',
    sources=['alarm_central_station_receiver/tigerjet/pytjapi.c']
)


def pyver():
    if version_info > (3, 0):
        return version_info.major

    return ''


setup(
    name='alarm_central_station_receiver',
    version='0.0.9',
    author='Chris Scuderi',
    license='Apache License Version 2.0',
    description='Software based central station receiver for home alarm systems',
    packages=find_packages(),
    ext_modules=[pytjapi],
    zip_safe=False,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'alarmd%s=alarm_central_station_receiver.main:main' % pyver(),
            'alarm-ctl%s=alarm_central_station_receiver.alarm_ctl:main' % pyver()
        ]
    },

    install_requires=[
        'pyaudio',
        'python-daemon-3k',
        'requests'
    ],
    extras_require={
        'RPI': ['RPi.GPIO']
    }
)
