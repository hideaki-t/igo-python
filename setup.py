#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup


setup(
    name='igo-python',
    version='0.9.2',
    description='Python port of Igo Japanese morphological analyzer',
    long_description=open('README').read() + "\n\n" + open('CHANGES').read(),
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
                 'Programming Language :: Python :: 2.5',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3.2',
                 'Topic :: Scientific/Engineering :: Information Analysis',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Topic :: Text Processing :: Linguistic',
                 ],
    keywords=['japanese', 'morphological analyzer', ],
    license='MIT',
    packages=['igo'],
    )
