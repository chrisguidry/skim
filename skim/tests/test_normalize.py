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
