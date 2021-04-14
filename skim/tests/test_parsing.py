import json
import os
import tempfile

import aiofiles
import pytest

from skim import parse


EXAMPLES_PATH = '/skim/skim/tests/examples/'

@pytest.mark.parametrize(
    'example,content_type',
    [
        ('w3c-example-rss-0.91', 'application/rss+xml'),
        ('w3c-example-rss-0.92', 'application/rss+xml'),
        ('w3c-example-rss-2.0', 'application/rss+xml'),
        ('ietf-short-atom-2005', 'application/atom+xml'),
        ('ietf-longer-atom-2005', 'application/atom+xml'),
    ]
)
async def test_parsing_standard_examples(example, content_type):
    example_filename = os.path.join(EXAMPLES_PATH, example + '.xml')
    expected_filename = os.path.join(EXAMPLES_PATH, example + '.json')

    async with aiofiles.open(expected_filename, 'r') as file:
       expected = json.loads(await file.read())

    async with aiofiles.open(example_filename, 'r') as file:
        feed, entries = await parse.parse(content_type, 'utf-8', file)

    assert feed == expected['feed']
    assert entries == expected['entries']


@pytest.mark.parametrize(
    'example',
    [
        'w3c-example-rss-0.91',
        'w3c-example-rss-0.92',
        'w3c-example-rss-2.0',
        'ietf-short-atom-2005',
        'ietf-longer-atom-2005',
    ]
)
async def test_parsing_standard_examples_generic_xml_type(example):
    example_filename = os.path.join(EXAMPLES_PATH, example + '.xml')
    expected_filename = os.path.join(EXAMPLES_PATH, example + '.json')

    async with aiofiles.open(expected_filename, 'r') as file:
       expected = json.loads(await file.read())

    async with aiofiles.open(example_filename, 'r') as file:
        feed, entries = await parse.parse('text/xml', 'utf-8', file)

    assert feed == expected['feed']
    assert entries == expected['entries']


async def test_raises_for_unknown_content_type():
    with pytest.raises(NotImplementedError):
        await parse.parse('text/plain', 'utf-8', None)


async def test_handles_empty_feed_document():
    with tempfile.NamedTemporaryFile('w') as weird_file:
        weird_file.write('')
        weird_file.flush()

        async with aiofiles.open(weird_file.name, 'r') as stream:
            feed, entries = await parse.parse(
                'application/rss+xml',
                'utf-8',
                stream
            )

        assert not feed
        assert not entries


async def test_raises_for_unrecognized_xml_document():
    with tempfile.NamedTemporaryFile('w') as weird_file:
        weird_file.write('<wat></wat>')
        weird_file.flush()

        async with aiofiles.open(weird_file.name, 'r') as stream:
            with pytest.raises(NotImplementedError):
                await parse.parse('text/xml', 'utf-8', stream)


async def test_handles_empty_xml_document():
    with tempfile.NamedTemporaryFile('w') as weird_file:
        weird_file.write('')
        weird_file.flush()

        async with aiofiles.open(weird_file.name, 'r') as stream:
            feed, entries = await parse.parse('text/xml', 'utf-8', stream)

        assert not feed
        assert not entries
