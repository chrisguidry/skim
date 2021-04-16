from datetime import datetime

import dateutil.parser
from dateutil.tz import gettz


def feed(feed):
    return {
        'title': (
            feed.get('title') or
            feed.get('atom:title')
        ),
        'site': (
            feed.get('link') or
            feed.get('atom:link') or
            feed.get('atom:link[alternate]')
        ),
        'icon': feed_icon(
            feed.get('logo') or
            feed.get('atom:icon') or
            feed.get('image')
        )
    }


def entry(entry):
    return {
        'id': (
            entry.get('id') or
            entry.get('atom:id') or
            entry.get('guid') or
            entry.get('uuid') or
            entry.get('link') or
            entry.get('atom:link[alternate]')
        ),
        'title': (
            entry.get('title') or
            entry.get('atom:title')
        ),
        'link': (
            entry.get('link') or
            entry.get('atom:link[alternate]')
        ),
        'timestamp': parse_date(
            entry.get('pubDate') or
            entry.get('atom:updated') or
            entry.get('atom:published') or
            datetime.utcnow().isoformat()
        ),
        'body': (
            entry.get('atom:content') or
            entry.get('content:encoded') or
            entry.get('content') or
            entry.get('atom:summary') or
            entry.get('summary') or
            entry.get('description')
        )
    }


def feed_icon(icon):
    if not icon:
        return None

    if isinstance(icon, str):
        return icon

    if isinstance(icon, dict):
        return icon.get('url')


def parse_date(datestring):
    tzinfos = {
        'EDT': gettz('America/New_York'),
        'EST': gettz('America/New_York')
    }
    return dateutil.parser.parse(datestring, tzinfos=tzinfos)
