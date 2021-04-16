from datetime import datetime

import dateutil.parser
from dateutil.tz import gettz


def feed(feed):
    return {
        'title': feed.get('title'),
        'site': (
            feed.get('link') or
            feed.get('link:alternate')
        ),
        'icon': feed.get('logo')
    }


def entry(entry):
    return {
        'id': (
            entry.get('id') or
            entry.get('guid') or
            entry.get('uuid') or
            entry.get('link') or
            entry.get('link:alternate')
        ),
        'title': entry.get('title'),
        'link': (
            entry.get('link') or
            entry.get('link:alternate')
        ),
        'timestamp': parse_date(
            entry.get('updated') or
            entry.get('pubDate') or
            entry.get('published') or
            datetime.utcnow().isoformat()
        ),
        'body': (
            entry.get('summary') or
            entry.get('description') or
            entry.get('content')
        )
    }


def parse_date(datestring):
    tzinfos = {
        'EDT': gettz('America/New_York'),
        'EST': gettz('America/New_York')
    }
    return dateutil.parser.parse(datestring, tzinfos=tzinfos)
