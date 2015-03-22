#coding: utf-8
from hashlib import md5
import logging
import sys
from urllib.parse import urlsplit, urlunsplit

from slugify import slugify

from skim.configuration import elastic
from skim.version import __version__


def logging_to_console(logger):
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(name)s %(message)s'))
    logger.addHandler(stream_handler)


def scrolled(*args, **kwargs):
    es = elastic()
    kwargs['scroll'] = kwargs.get('scroll') or '10s'
    results = es.search(*args, **kwargs)
    while results['hits']['hits']:
        for hit in results['hits']['hits']:
            yield hit['_source']
        results = es.scroll(scroll_id=results['_scroll_id'], scroll=kwargs['scroll'])
