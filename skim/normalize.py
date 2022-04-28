import html
from datetime import timezone
from urllib.parse import urljoin, urlparse

import dateutil.parser
from bs4 import BeautifulSoup
from dateutil.tz import gettz

from skim import dates


def feed(feed):
    return {
        'title': title(
            feed.get('title') or feed.get('atom:title') or feed.get('description')
        ),
        'site': (
            feed.get('link')
            or feed.get('atom:link')
            or feed.get('atom:link[alternate]')
        ),
        'icon': feed_icon(
            feed.get('logo') or feed.get('atom:icon') or feed.get('image')
        ),
        'caching': feed.get('skim:caching'),
    }


def entry(entry):
    link = (
        entry.get('link')
        or entry.get('atom:link[alternate]')
        or urllike(entry.get('id'))
        or urllike(entry.get('atom:id'))
        or urllike(entry.get('guid'))
    )
    return {
        'id': (
            entry.get('id')
            or entry.get('atom:id')
            or entry.get('guid')
            or entry.get('link')
            or entry.get('atom:link[alternate]')
        ),
        'title': title(entry.get('title') or entry.get('atom:title')),
        'link': link,
        'timestamp': entry_date(
            entry.get('pubDate')
            or entry.get('atom:updated')
            or entry.get('atom:published')
            or dates.utcnow().isoformat()
        ),
        'creators': list_or_none(
            creators(entry.get('dc:creator') or entry.get('atom:author'))
        ),
        'categories': list_or_none(entry.get('category')),
        'body': markup(
            entry.get('atom:content')
            or entry.get('content:encoded')
            or entry.get('content')
            or entry.get('atom:summary')
            or entry.get('summary')
            or entry.get('description')
            or youtube_embed(entry),
            enclosures=entry.get('enclosure'),
            base_url=link,
        ),
    }


def feed_icon(icon):
    if not icon:
        return None

    if isinstance(icon, str):
        return icon

    if isinstance(icon, dict):
        return icon.get('url')

    return None


def entry_date(datestring):
    tzinfos = {
        'EDT': gettz('America/New_York'),
        'EST': gettz('America/New_York'),
    }
    parsed = dateutil.parser.parse(datestring, tzinfos=tzinfos)

    # if the feed doesn't have a timezone, assume Eastern
    if not parsed.tzinfo:
        parsed = parsed.replace(tzinfo=tzinfos['EST'])

    # if the feed seems to only be giving dates, use the crawl time as the
    # timestamp if we're crawling it on the same day the article is first seen
    now = dates.utcnow()
    age = now - parsed
    if age.total_seconds() < 86400 and (parsed.hour, parsed.minute) == (0, 0):
        parsed = now

    return parsed.astimezone(timezone.utc)


def creators(values):
    values = list_or_none(values)
    if not values:
        return values

    return [item for item in map(creator, values) if item]


def creator(value):
    if not value:
        return None
    if isinstance(value, dict):
        return value.get('atom:name')
    return str(value)


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
    <div class="youtube video">
      <iframe src="https://www.youtube.com/embed/{video_id}" allowfullscreen>
      </iframe>
    </div>
    '''


def title(content):
    if not content:
        return content

    soup = BeautifulSoup(content, features='html.parser')
    return html.unescape(soup.prettify().strip())


def markup(content, base_url='', enclosures=None):
    if not content and not enclosures:
        return content

    content = (content or '').strip()

    # when the result seems like just plain text, wrap it in paragraphs
    if content and '<' not in content and '>' not in content:
        content = content.replace('\n\n', '\n')
        content = '<p>' + '</p><p>'.join(content.split('\n')) + '</p>'

    soup = BeautifulSoup(content, features='html.parser')

    enclosures = list_or_none(enclosures)
    if enclosures:
        tags = [embed_enclosure(soup, enclosure) for enclosure in enclosures]
        for i, tag in enumerate(filter(None, tags)):
            soup.insert(i, tag)

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


def embed_enclosure(soup, enclosure):
    url = enclosure.get('url') or enclosure.get('href')
    media_type = enclosure.get('type')
    if not url or not media_type:
        return None

    if media_type.startswith('image/'):
        tag = soup.new_tag('picture')
        source = soup.new_tag('img', src=url)
    elif media_type.startswith('audio/'):
        tag = soup.new_tag('audio')
        tag['controls'] = None
        source = soup.new_tag('source', src=url, type=media_type)
    elif media_type.startswith('video/'):
        tag = soup.new_tag('video')
        tag['controls'] = None
        source = soup.new_tag('source', src=url, type=media_type)
    else:
        print('Unrecognized enclosure media type {media_type!r}')
        return None

    tag['class'] = 'enclosure'
    tag.append(source)

    return tag
