#!/usr/bin/env python3

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "wasnnu",
    version = "0.0.2",
    author = "Leonard Göhrs",
    author_email = "leonard@goehrs.eu",
    description = "A plain text, commandline based python time tracking software",
    license = "GPLv3+",
    keywords = "time-tracker plaintext",
    url = "https://github.com/hnez/Wasnnu",
    packages=['wasnnu'],
    long_description=read('README.md'),
    entry_points = {
        'console_scripts' : [
            'wasnnu=wasnnu:main'
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Utilities",
    ],
)
