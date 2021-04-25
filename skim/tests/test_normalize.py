from datetime import datetime

import time_machine

from skim import normalize

FROZEN_NOW = datetime.utcnow()


def test_feed_empty():
    normalized = normalize.feed({})
    assert normalized == {
        'title': None,
        'site': None,
        'icon': None,
        'caching': None,
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


@time_machine.travel(FROZEN_NOW)
def test_entry_empty():
    normalized = normalize.entry({})
    assert normalized == {
        'id': None,
        'title': None,
        'link': None,
        'timestamp': FROZEN_NOW,
        'body': None
    }


def test_normalizing_links_with_urllike_id():
    normalized = normalize.entry({
        'id': 'https://example.com/1'
    })
    assert normalized['link'] == 'https://example.com/1'


def test_normalizing_youtube_feeds():
    normalized = normalize.entry({
        'atom:id': 'yt:video:abcdefg'
    })
    assert normalized['body'] == (
        '<iframe allowfullscreen="" '
        'class="youtube video" '
        'src="https://www.youtube.com/embed/abcdefg">\n'
        '</iframe>\n'
    )


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
