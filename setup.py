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
        'beautifulsoup4==4.3.2',
        'cssmin==0.2.0',
        'Flask==0.10.1',
        'Flask-Assets==0.10',
        'flask-debugtoolbar==0.9.2',
        'feedparser==5.2.0.post1',
        'html2text==2015.4.14',
        'html5lib==0.999',
        'Markdown==2.6',
        'python-slugify==1.0.2',
        'pyembed==1.1.2',
        'pygments==2.0.2',
        'Whoosh==2.7.0'
    ]
)
