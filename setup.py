#!/usr/bin/env python

from setuptools import setup

setup(
    name='bzcompliance',
    version='1.0',
    description='OpenShift App',
    author='Matthew Owens',
    author_email='mowens@redhat.com',
    url='http://www.python.org/sigs/distutils-sig/',
    install_requires=['Django<=1.4', 'beautifulsoup4'],
)
