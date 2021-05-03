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
        'caching': None
    }


def test_feed_basics():
    normalized = normalize.feed({
        'title': 'The Title',
        'link': 'https://example.com/1',
        'logo': 'https://example.com/logo.png'
    })
    assert normalized == {
        'title': 'The Title',
        'site': 'https://example.com/1',
        'icon': 'https://example.com/logo.png',
        'caching': None
    }


def test_feed_detailed_icon():
    normalized = normalize.feed({
        'title': 'The Title',
        'link': 'https://example.com/1',
        'image': {
            'url': 'https://example.com/logo.png'
        }
    })
    assert normalized == {
        'title': 'The Title',
        'site': 'https://example.com/1',
        'icon': 'https://example.com/logo.png',
        'caching': None
    }


def test_feed_detailed_icon_not_a_string_or_dict():
    normalized = normalize.feed({
        'title': 'The Title',
        'link': 'https://example.com/1',
        'image': [
            'nope', 'https://example.com/logo.png'
        ]
    })
    assert normalized == {
        'title': 'The Title',
        'site': 'https://example.com/1',
        'icon': None,
        'caching': None
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
        'categories': None
    }


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
    normalized = normalize.entry({
        'id': 'https://example.com/1'
    })
    assert normalized['link'] == 'https://example.com/1'


def test_normalizing_date_only_on_an_earlier_day():
    normalized = normalize.entry({
        'pubDate': 'April 1st, 2021'
    })
    eastern = gettz('America/New_York')
    assert normalized['timestamp'] == datetime(2021, 4, 1, tzinfo=eastern)


@mock.patch('skim.dates.utcnow', return_value=FROZEN_NOW)
def test_normalizing_date_only_today(utcnow):
    normalized = normalize.entry({
        'pubDate': FROZEN_NOW.strftime('%B %d, %Y')
    })
    assert normalized['timestamp'] == FROZEN_NOW


def test_normalizing_youtube_feeds():
    normalized = normalize.entry({
        'atom:id': 'yt:video:abcdefg'
    })
    assert normalized['body'] == BeautifulSoup('''
    <div class="youtube video">
        <iframe allowfullscreen src="https://www.youtube.com/embed/abcdefg">
        </iframe>
    </div>
    ''', features='html.parser').prettify()


def test_normalizing_markup_relative_links():
    normalized = normalize.entry({
        'link': 'https://example.com/1',
        'content': (
            '<a href="/1/2/3/">'
            '<img src="4/5/6"/>'
            '<img src="https://leaveit" />'
            '</a>'
        )
    })
    assert normalized['body'] == (
        '<a href="https://example.com/1/2/3/">\n'
        ' <img src="https://example.com/4/5/6"/>\n'
        ' <img src="https://leaveit"/>\n'
        '</a>'
    )


def test_normalizing_scrubbing_google_analytics_images():
    normalized = normalize.entry({
        'link': 'https://example.com/1',
        'content': (
            '<p>'
            '<em>hello</em>'
            '<img src="https://www.google-analytics.com/booooooo"/>'
            '<em>world</em>'
            '</p>'
        )
    })
    assert normalized['body'] == (
        '<p>\n'
        ' <em>\n'
        '  hello\n'
        ' </em>\n'
        ' <em>\n'
        '  world\n'
        ' </em>\n'
        '</p>'
    )
