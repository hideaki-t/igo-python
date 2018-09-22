#!/usr/bin/env python
# encoding: utf-8

import io
from setuptools import setup

setup(
    name='igo-python',
    version='1.0.0',
    description='Python port of Igo Japanese morphological analyzer',
    long_description=io.open('README', encoding='utf-8').read() + "\n\n" +
    io.open('CHANGES', encoding='utf-8').read(),
    author='Hideaki Takahashi',
    author_email='mymelo@gmail.com',
    url='https://github.com/hideaki-t/igo-python/',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Japanese',
        'Operating System :: OS Independent',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: IronPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
    ],
    keywords=[
        'japanese',
        'morphological analyzer',
    ],
    license='MIT',
    packages=['igo'],
    package_data={'igo': ['ipadic/*']},
    entry_points={'console_scripts': ['igo = igo.parse:main']})
