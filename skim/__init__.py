#coding: utf-8

from contextlib import contextmanager
import os
from os.path import join
from urllib.parse import urlparse

from slugify import slugify

from skim.version import __version__


def slug(url):
    scheme, netloc, *components = urlparse(url)
    netloc = '.'.join(reversed(netloc.split('.')))
    return slugify('-'.join((scheme, netloc) + tuple(components)))

def unique(iterable, key=lambda x: x):
    seen = set()
    for item in iterable:
        value = key(item)
        if value in seen:
            continue
        yield item
        seen.add(value)

@contextmanager
def open_file_from(directory, filename, mode):
    for tried in (False, True):
        try:
            with open(join(directory, filename), mode=mode) as f:
                yield f
        except OSError:
            if tried or os.path.exists(directory):
                raise
            os.makedirs(directory)
            continue
        return
