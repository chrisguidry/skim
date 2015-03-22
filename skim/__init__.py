#coding: utf-8
from hashlib import md5
import logging
import sys
from urllib.parse import urlsplit, urlunsplit

from slugify import slugify

from skim.version import __version__


def key(url):
    split = list(urlsplit(url))
    split[0] = ''
    split[1] = '.'.join(reversed(split[1].split('.')))
    return slugify(urlunsplit(split))

def logging_to_console(logger):
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(name)s %(message)s'))
    logger.addHandler(stream_handler)
