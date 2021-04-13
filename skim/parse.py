import asyncio
from xml.etree import ElementTree


XML_FEEDS = {
    'application/atom+xml',
    'application/rss+xml',
    'application/xml',
    'text/xml'
}


async def parse(response):
    """Given an HTTP Response, parse the feed and entries of the RSS feed,
    yielding each as a pair."""
    if response.content_type in XML_FEEDS:
        return await parse_xml_feed(response)

    else:
        raise NotImplementedError(
            f'Parsing feeds of type "{response.content_type}" is not '
            'implemented'
        )


async def xml_elements_from_response(response):
    parser = ElementTree.XMLPullParser(['start', 'end'])
    while not response.content.at_eof():
        parser.feed(await response.content.read(1024))
        for event, element in parser.read_events():
            yield event, element


ATOM_NS = '{http://www.w3.org/2005/Atom}'
XML_FORMATS = {
    'application/rss+xml': {
        'feed_path': ['rss', 'channel'],
        'entries_key': 'item'
    },
    'application/atom+xml': {
        'feed_path': ['feed'],
        'entries_key': 'entry'
    }
}

async def parse_xml_feed(response):
    """Parse an XML-based feed, like an RSS or Atom feed, returning a feed and
    its entries as a pair"""
    stack = [{}]

    xml_format = XML_FORMATS.get(response.content_type)

    async for event, element in xml_elements_from_response(response):
        tag = element.tag.replace(ATOM_NS, '')
        child_name = tag

        # since we couldn't determine the feed format from the Content-Type,
        # guess it from the root element, or stop now
        if not xml_format:
            for xml_format in XML_FORMATS.values():
                if tag == xml_format['feed_path'][0]:
                    break
            else:
                raise NotImplementedError(
                    f'Unrecognized XML feed format "{response.content_type}"'
                )

        if event == 'start':
            stack.append({})

        elif event == 'end':
            child = stack.pop()

            # process text elements

            # TODO: handle Atom's type="text" and type="html"
            # TODO: handle Atom's link tag more accurately, including rel=
            if f'{ATOM_NS}href' in element.attrib:
                child['__value__'] = element.attrib[f'{ATOM_NS}href']
            elif 'href' in element.attrib:
                child['__value__'] = element.attrib['href']
            else:
                child['__value__'] = (element.text or '').strip()

            if f'{ATOM_NS}rel' in element.attrib:
                child_name = f'{child_name}:{element.attrib[f"{ATOM_NS}rel"]}'
            elif 'rel' in element.attrib:
                child_name = f'{child_name}:{element.attrib["rel"]}'

            # if the only thing in this child is a `__value__` key, just use
            # that as the child
            if set(child.keys()) == {'__value__'}:
                child = child['__value__']
            elif not child['__value__']:
                child.pop('__value__')

            # integrate the new child into the parent
            parent = stack[-1]
            if child_name in parent:
                if isinstance(parent[child_name], list):
                    parent[child_name].append(child)
                else:
                    parent[child_name] = [parent[child_name], child]
            else:
                parent[child_name] = child

    assert len(stack) == 1

    feed = stack[0]
    for step in xml_format['feed_path']:
        feed = feed[step]

    entries = feed.pop(xml_format['entries_key'])

    return feed, entries
