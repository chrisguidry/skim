from datetime import datetime

import time_machine

from skim import normalize

FROZEN_NOW = datetime.utcnow()


def test_feed_empty():
    normalized = normalize.feed({})
    assert normalized == {
        'title': None,
        'site': None,
        'icon': None
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
        'icon': 'https://example.com/logo.png'
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
        'icon': 'https://example.com/logo.png'
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
        'icon': None
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
