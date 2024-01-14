from datetime import datetime
from unittest import mock

from bs4 import BeautifulSoup
from dateutil.tz import gettz

from skim import dates, normalize

FROZEN_NOW = dates.utcnow()


def test_feed_empty():
    normalized = normalize.feed({})
    assert normalized == {
        'title': None,
        'site': None,
        'icon': None,
        'caching': None,
    }


def test_feed_basics():
    normalized = normalize.feed(
        {
            'title': 'The Title',
            'link': 'https://example.com/1',
            'logo': 'https://example.com/logo.png',
        }
    )
    assert normalized == {
        'title': 'The Title',
        'site': 'https://example.com/1',
        'icon': 'https://example.com/logo.png',
        'caching': None,
    }


def test_feed_detailed_icon():
    normalized = normalize.feed(
        {
            'title': 'The Title',
            'link': 'https://example.com/1',
            'image': {'url': 'https://example.com/logo.png'},
        }
    )
    assert normalized == {
        'title': 'The Title',
        'site': 'https://example.com/1',
        'icon': 'https://example.com/logo.png',
        'caching': None,
    }


def test_feed_detailed_icon_not_a_string_or_dict():
    normalized = normalize.feed(
        {
            'title': 'The Title',
            'link': 'https://example.com/1',
            'image': ['nope', 'https://example.com/logo.png'],
        }
    )
    assert normalized == {
        'title': 'The Title',
        'site': 'https://example.com/1',
        'icon': None,
        'caching': None,
    }


@mock.patch('skim.dates.utcnow', return_value=FROZEN_NOW)
def test_entry_empty(utcnow):
    normalized = normalize.entry({})
    assert normalized == {
        'id': None,
        'title': None,
        'link': None,
        'timestamp': FROZEN_NOW,
        'body': None,
        'creators': None,
        'categories': None,
    }


def test_normalizing_titles():
    assert normalize.title('hello &amp; world') == 'hello & world'
    assert normalize.title('hello & world') == 'hello & world'
    assert normalize.title('hello &lt; world') == 'hello < world'
    assert normalize.title('hello < world') == 'hello < world'
    assert normalize.title('hello &gt; world') == 'hello > world'
    assert normalize.title('hello > world') == 'hello > world'
    assert normalize.title('<em>hello</em>') == '<em>\n hello\n</em>'
    # a goofy thing observed on a real feed
    assert normalize.title('and#039;foo and#042; barand#039;') == "'foo * bar'"


def test_normalizing_lists():
    normalized = normalize.entry({})
    assert normalized['creators'] is None

    normalized = normalize.entry({'dc:creator': None})
    assert normalized['creators'] is None

    normalized = normalize.entry({'dc:creator': 'Jane'})
    assert normalized['creators'] == ['Jane']

    normalized = normalize.entry({'dc:creator': ['Jane', 'John']})
    assert normalized['creators'] == ['Jane', 'John']


def test_normalizing_links_with_urllike_id():
    normalized = normalize.entry({'id': 'https://example.com/1'})
    assert normalized['link'] == 'https://example.com/1'


def test_normalizing_date_only_on_an_earlier_day():
    normalized = normalize.entry({'pubDate': 'April 1st, 2021'})
    eastern = gettz('America/New_York')
    assert normalized['timestamp'] == datetime(2021, 4, 1, tzinfo=eastern)


@mock.patch('skim.dates.utcnow', return_value=FROZEN_NOW)
def test_normalizing_date_only_today(utcnow):
    normalized = normalize.entry({'pubDate': FROZEN_NOW.strftime('%B %d, %Y')})
    assert normalized['timestamp'] == FROZEN_NOW


def test_normalizing_null_creators():
    normalized = normalize.entry({})
    assert normalized['creators'] is None

    normalized = normalize.entry({'atom:author': [None]})
    assert normalized['creators'] is None

    normalized = normalize.entry({'atom:author': ['']})
    assert normalized['creators'] is None

    normalized = normalize.entry({'atom:author': {}})
    assert normalized['creators'] is None

    normalized = normalize.entry({'atom:author': []})
    assert normalized['creators'] is None

    normalized = normalize.entry({'atom:author': {}})
    assert normalized['creators'] is None


def test_normalizing_single_creators():
    normalized = normalize.entry({'atom:author': {'atom:name': 'Jiminy Crickets'}})
    assert normalized['creators'] == ['Jiminy Crickets']


def test_normalizing_multiple_creators():
    normalized = normalize.entry(
        {
            'atom:author': [
                {'atom:name': 'Jiminy Crickets'},
                {'atom:name': 'Criminy Jickets'},
            ],
        }
    )
    assert normalized['creators'] == ['Jiminy Crickets', 'Criminy Jickets']


def test_normalizing_youtube_feeds():
    normalized = normalize.entry({'atom:id': 'yt:video:abcdefg'})
    assert (
        normalized['body']
        == BeautifulSoup(
            '''
    <div class="youtube video">
        <iframe allowfullscreen src="https://www.youtube.com/embed/abcdefg">
        </iframe>
    </div>''',
            features='html.parser',
        ).prettify()
    )


def test_normalizing_markup_relative_links():
    normalized = normalize.entry(
        {
            'link': 'https://example.com/1',
            'content': (
                '<a href="/1/2/3/">'
                '<img src="4/5/6"/>'
                '<img src="https://leaveit" />'
                '</a>'
            ),
        }
    )
    assert normalized['body'] == '\n'.join(
        [
            '<a href="https://example.com/1/2/3/">',
            ' <img src="https://example.com/4/5/6"/>',
            ' <img src="https://leaveit"/>',
            '</a>',
        ]
    )


def test_normalizing_scrubbing_google_analytics_images():
    normalized = normalize.entry(
        {
            'link': 'https://example.com/1',
            'content': (
                '<p>'
                '<em>hello</em>'
                '<img src="https://www.google-analytics.com/booooooo"/>'
                '<em>world</em>'
                '</p>'
            ),
        }
    )
    assert normalized['body'] == '\n'.join(
        [
            '<p>',
            ' <em>',
            '  hello',
            ' </em>',
            ' <em>',
            '  world',
            ' </em>',
            '</p>',
        ]
    )


def test_normalizing_markup_plain_text_wrapped_in_a_paragraph():
    normalized = normalize.entry({'content': 'Hello, world!'})
    assert normalized['body'] == ('<p>\n Hello, world!\n</p>')

    normalized = normalize.entry(
        {
            'content': """
            Hello, world!

            This is awesome!
        """
        }
    )
    assert normalized['body'] == (
        '<p>\n Hello, world!\n</p>\n' '<p>\n This is awesome!\n</p>'
    )


def test_embedding_empty_enclosure():
    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': None,
        }
    )
    assert normalized['body'] == '<p>\n Hello, world!\n</p>'

    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': {},
        }
    )
    assert normalized['body'] == '<p>\n Hello, world!\n</p>'

    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': {'foo': 'bar'},
        }
    )
    assert normalized['body'] == '<p>\n Hello, world!\n</p>'

    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': {'url': 'foo', 'type': None},
        }
    )
    assert normalized['body'] == '<p>\n Hello, world!\n</p>'

def test_embedding_unrecognized_media_type():
    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': {'url': 'https://example.com/wut', 'type': 'foo/bar'},
        }
    )
    assert normalized['body'] == '<p>\n Hello, world!\n</p>'


def test_embedding_single_image_enclosure():
    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': {
                'href': 'http://example.com/image.png',
                'type': 'image/png',
            },
        }
    )
    assert normalized['body'] == '\n'.join(
        [
            '<picture class="enclosure">',
            ' <img src="http://example.com/image.png"/>',
            '</picture>',
            '<p>',
            ' Hello, world!',
            '</p>',
        ]
    )


def test_embedding_single_image_enclosure_with_url():
    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': {
                'url': 'http://example.com/image.png',
                'type': 'image/png',
            },
        }
    )
    assert normalized['body'] == '\n'.join(
        [
            '<picture class="enclosure">',
            ' <img src="http://example.com/image.png"/>',
            '</picture>',
            '<p>',
            ' Hello, world!',
            '</p>',
        ]
    )


def test_embedding_multiple_image_enclosures():
    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': [
                {
                    'href': 'http://example.com/image-1.png',
                    'type': 'image/png',
                },
                {
                    'href': 'http://example.com/image-2.png',
                    'type': 'image/png',
                },
            ],
        }
    )
    assert normalized['body'] == '\n'.join(
        [
            '<picture class="enclosure">',
            ' <img src="http://example.com/image-1.png"/>',
            '</picture>',
            '<picture class="enclosure">',
            ' <img src="http://example.com/image-2.png"/>',
            '</picture>',
            '<p>',
            ' Hello, world!',
            '</p>',
        ]
    )


def test_skipping_enclosures_already_in_content():
    normalized = normalize.entry(
        {
            'content': 'Hello, world! http://example.com/image-1.png is pretty, right?',
            'enclosure': [
                {
                    'href': 'http://example.com/image-1.png',
                    'type': 'image/png',
                },
                {
                    'href': 'http://example.com/image-2.png',
                    'type': 'image/png',
                },
            ],
        }
    )
    assert normalized['body'] == '\n'.join(
        [
            '<picture class="enclosure">',
            ' <img src="http://example.com/image-2.png"/>',
            '</picture>',
            '<p>',
            ' Hello, world! http://example.com/image-1.png is pretty, right?',
            '</p>',
        ]
    )


def test_embedding_single_audio_enclosure():
    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': {
                'href': 'http://example.com/yay.mp3',
                'type': 'audio/mpeg',
            },
        }
    )
    assert normalized['body'] == '\n'.join(
        [
            '<audio class="enclosure" controls>',
            ' <source src="http://example.com/yay.mp3" type="audio/mpeg"/>',
            '</audio>',
            '<p>',
            ' Hello, world!',
            '</p>',
        ]
    )


def test_embedding_single_video_enclosure():
    normalized = normalize.entry(
        {
            'content': 'Hello, world!',
            'enclosure': {
                'href': 'http://example.com/yay.mpeg',
                'type': 'video/mpeg',
            },
        }
    )
    assert normalized['body'] == '\n'.join(
        [
            '<video class="enclosure" controls>',
            ' <source src="http://example.com/yay.mpeg" type="video/mpeg"/>',
            '</video>',
            '<p>',
            ' Hello, world!',
            '</p>',
        ]
    )
