#coding: utf-8

import os
import tempfile

import pytest

from skim import open_file_from, slug, unique


def test_slugifying_url():
    assert slug('https://s.d.tld/feed.xml') == 'https-tld-d-s-feed-xml'
    assert slug('ftp://s.d.tld/feed.xml') == 'ftp-tld-d-s-feed-xml'
    assert (slug('http://subdomain.domain.tld/path-1/path-2?query=value#fragment') ==
            'http-tld-domain-subdomain-path-1-path-2-query-value-fragment')

def test_unique():
    assert list(unique([1, 2, 3])) == [1, 2, 3]
    assert list(unique([1, 2, 1, 2])) == [1, 2]

def test_unique_with_key():
    first = {'a': '1', 'b': '1'}
    second = {'a': '2', 'b': '2'}
    third = {'a': '3', 'b': '1'}
    items = [first, second, third]

    assert list(unique(items, key=lambda v: v['a'])) == [first, second, third]
    assert list(unique(items, key=lambda v: v['b'])) == [first, second]


def test_open_from_directory_not_exists():
    directory = tempfile.mkdtemp()
    with open_file_from(os.path.join(directory, 'extra'), 'hello', mode='w') as f:
        f.write('world')
    with open(os.path.join(directory, 'extra', 'hello'), 'r') as f:
        assert f.read() == 'world'

def test_open_from_directory_exists():
    directory = tempfile.mkdtemp()
    with open_file_from(os.path.join(directory), 'hello', mode='w') as f:
        f.write('world')
    with open(os.path.join(directory, 'hello'), 'r') as f:
        assert f.read() == 'world'

def test_open_from_file_does_not_exist():
    directory = tempfile.mkdtemp()
    with pytest.raises(FileNotFoundError):
        with open_file_from(os.path.join(directory), 'hello', mode='r') as f:
            pass  # pragma: no cover
