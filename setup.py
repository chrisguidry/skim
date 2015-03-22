#!/usr/bin/env python
#coding: utf-8
import os.path
from setuptools import setup, find_packages

__version__ = ''
with open(os.path.join(os.path.dirname(__file__), 'skim', 'version.py')) as version_file:
    exec(version_file.read())

setup(
    name='skim',
    description='skim, a self-hosted news reader',
    url='https://github.com/chrisguidry/skim',
    author='Chris Guidry',
    author_email='chris@theguidrys.us',
    version=__version__,
    packages=find_packages(),
    install_requires=[
        'elasticsearch==1.4.0',
        'Flask==0.10.1',
        'Flask-Assets==0.10',
        'feedparser==5.1.3',
        'html2text==2015.2.18',
        'Markdown==2.6',
        'pygments==2.0.2',
        'python-slugify==0.1.0'
    ]
)
