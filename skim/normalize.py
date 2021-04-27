from datetime import datetime
from urllib.parse import urljoin, urlparse

import dateutil.parser
from bs4 import BeautifulSoup
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
        ),
        'caching': feed.get('skim:caching')
    }


def entry(entry):
    link = (
        entry.get('link') or
        entry.get('atom:link[alternate]') or
        urllike(entry.get('id')) or
        urllike(entry.get('atom:id')) or
        urllike(entry.get('guid'))
    )
    return {
        'id': (
            entry.get('id') or
            entry.get('atom:id') or
            entry.get('guid') or
            entry.get('link') or
            entry.get('atom:link[alternate]')
        ),
        'title': (
            entry.get('title') or
            entry.get('atom:title')
        ),
        'link': link,
        'timestamp': date(
            entry.get('pubDate') or
            entry.get('atom:updated') or
            entry.get('atom:published') or
            datetime.utcnow().isoformat()
        ),
        'creators': list_or_none(
            entry.get('dc:creator') or
            entry.get('atom:author', {}).get('atom:name')
        ),
        'categories': list_or_none(
            entry.get('category')
        ),
        'body': markup(
            entry.get('atom:content') or
            entry.get('content:encoded') or
            entry.get('content') or
            entry.get('atom:summary') or
            entry.get('summary') or
            entry.get('description') or
            youtube_embed(entry),
            base_url=link
        )
    }


def feed_icon(icon):
    if not icon:
        return None

    if isinstance(icon, str):
        return icon

    if isinstance(icon, dict):
        return icon.get('url')


def date(datestring):
    tzinfos = {
        'EDT': gettz('America/New_York'),
        'EST': gettz('America/New_York')
    }
    return dateutil.parser.parse(datestring, tzinfos=tzinfos)


def urllike(string):
    if not string:
        return None

    parsed = urlparse(string)
    if parsed.scheme and parsed.netloc:
        return string

    return None


def list_or_none(value):
    if not value:
        return None
    if not isinstance(value, list):
        return [value]
    return value


def youtube_embed(entry):
    entry_id = entry.get('atom:id')
    if not entry_id or not entry_id.startswith('yt:video:'):
        return None

    video_id = entry_id.split(':')[-1]

    return f'''
    <iframe src="https://www.youtube.com/embed/{video_id}"
            class="youtube video"
            allowfullscreen>
    </iframe>
    '''


def markup(content, base_url):
    if not content:
        return content

    soup = BeautifulSoup(content, features='html.parser')

    # translate relative URLs to absolute URLs
    for attribute in ['href', 'src']:
        for element in soup.select(f'[{attribute}]'):
            parsed = urlparse(element[attribute])
            if not parsed.scheme:
                element[attribute] = urljoin(base_url, element[attribute])

    # scrub any <img src="...google analytics..." /> trackers
    for element in soup.select('img[src]'):
        parsed = urlparse(element['src'])
        if parsed.netloc == 'www.google-analytics.com':
            element.decompose()

    return soup.prettify()
