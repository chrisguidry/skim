#!/usr/bin/env python
#coding: utf-8
import os.path
from setuptools import setup, find_packages

__version__ = ''
with open(os.path.join(os.path.dirname(__file__), 'skim', 'version.py')) as version_file:
    exec(version_file.read())

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as requirements_file:
    requires = [line for line in map(str.strip, requirements_file.readlines())
                if line and not line.startswith('#')]

setup(
    name='skim',
    description='skim, a self-hosted news reader',
    url='https://github.com/chrisguidry/skim',
    author='Chris Guidry',
    author_email='chris@theguidrys.us',
    version=__version__,
    packages=find_packages(),
    install_requires=requires
)
