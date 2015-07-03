#!/usr/bin/env python
# encoding: utf-8

import io
from setuptools import setup


setup(
    name='igo-python',
    version='0.9.6',
    description='Python port of Igo Japanese morphological analyzer',
    long_description=io.open('README', encoding='utf-8').read() + "\n\n" + io.open('CHANGES', encoding='utf-8').read(),
    author='Hideaki Takahashi',
    author_email='mymelo@gmail.com',
    url='https://github.com/hideaki-t/igo-python/',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: MIT License',
                 'Natural Language :: Japanese',
                 'Operating System :: OS Independent',
                 'Operating System :: Microsoft :: Windows',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: IronPython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Scientific/Engineering :: Information Analysis',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Topic :: Text Processing :: Linguistic',
                 ],
    keywords=['japanese', 'morphological analyzer', ],
    license='MIT',
    packages=['igo'],
    )
