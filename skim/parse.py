import asyncio
from xml.etree import ElementTree


XML_FEEDS = {'application/rss+xml', 'application/atom+xml'}


async def parse(response):
    """Given an HTTP Response, parse the feed and entries of the RSS feed,
    yielding each as a pair."""
    if response.content_type in XML_FEEDS:
        return await parse_xml_feed(response)

    else:
        raise NotImplementedError(
            f'Parsing content of type "{response.content_type}" is not '
            'implemented'
        )

async def xml_elements_from_response(response):
    parser = ElementTree.XMLPullParser(['start', 'end'])
    while not response.content.at_eof():
        parser.feed(await response.content.read(1024))
        for event, element in parser.read_events():
            yield event, element

async def parse_xml_feed(response):
    """Parse an XML-based feed, like an RSS or Atom feed, returning a feed and
    its entries as a pair"""
    stack = [{}]

    ATOM = '{http://www.w3.org/2005/Atom}'

    if response.content_type == 'application/rss+xml':
        FEED_PATH = ['rss', 'channel']
        ENTRIES_KEY = 'item'

    elif response.content_type == 'application/atom+xml':
        FEED_PATH = ['feed']
        ENTRIES_KEY = 'entry'

    else:
        raise NotImplementedError(
            f'XML parsing content of type "{response.content_type}" is not '
            'implemented'
        )

    async for event, element in xml_elements_from_response(response):
        tag = element.tag.replace(ATOM, '')

        if event == 'start':
            stack.append({})

        elif event == 'end':
            # process text elements

            # TODO: handle Atom's type="text" and type="html"
            # TODO: handle Atom's link tag more accurately, including rel=

            current = stack[-1]
            if f'{ATOM}href' in element.attrib:
                current['__value__'] = element.attrib[f'{ATOM}href']
            else:
                current['__value__'] = element.text

            # we're finished with this child element, let's pop back up to
            # its parent and integrate it
            child = stack.pop()

            # if the only thing in this child is a `__value__` key, just use
            # that as the child
            if set(child.keys()) == {'__value__'}:
                child = child['__value__']
            elif child['__value__'] is None:
                child.pop('__value__')

            # integrate the new child into the parent
            parent = stack[-1]
            if tag in parent:
                if isinstance(parent[tag], list):
                    parent[tag].append(child)
                else:
                    parent[tag] = [parent[tag], child]
            else:
                parent[tag] = child

    assert len(stack) == 1

    feed = stack[0]
    for step in FEED_PATH:
        feed = feed[step]

    entries = feed.pop(ENTRIES_KEY)

    return feed, entries
