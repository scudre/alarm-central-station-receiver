from setuptools import setup, find_packages

setup(
    name='alarm_central_station_receiver',
    version='0.0.5',
    author='Chris Scuderi',
    license='Apache License Version 2.0',
    description='Software based central station receiver for home alarm systems',
    packages=find_packages(),
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
