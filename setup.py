from setuptools import setup, find_packages, Extension

pytjapi = Extension(
    'pytjapi',
    sources=['alarm_central_station_receiver/tigerjet/pytjapi.c']
)

setup(
    name='alarm_central_station_receiver',
    version='0.0.6',
    author='Chris Scuderi',
    license='Apache License Version 2.0',
    description='Software based central station receiver for home alarm systems',
    packages=find_packages(),
    ext_modules=[pytjapi],
    zip_safe=False,
    include_package_data=True,
    entry_points = {
        'console_scripts': ['alarmd=alarm_central_station_receiver.main:main']
        },
    install_requires = [
        'RPi.GPIO',
        'pyaudio',
        'python-daemon'
    ]
)
