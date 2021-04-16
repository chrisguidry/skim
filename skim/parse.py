from xml.etree import ElementTree

XML_FEEDS = {
    'application/atom+xml',
    'application/rss+xml',
    'application/xml',
    'text/xml'
}


async def parse(content_type, charset, stream):
    """Given the type, character set, and a stream of content, parse the feed
    and entries of the feed, yielding each as a pair."""
    if content_type in XML_FEEDS:
        return await parse_xml_feed(content_type, charset, stream)

    else:
        raise NotImplementedError(
            f'Parsing feeds of type "{content_type}" is not '
            'implemented'
        )


async def xml_from_stream(stream, events):
    parser = ElementTree.XMLPullParser(events)
    while chunk := await stream.read(1024):
        # clean known problematic characters
        chunk = chunk.replace(b'\x08', b'')
        parser.feed(chunk)
        for event, element in parser.read_events():
            yield event, element


XML_FORMATS = {
    'application/rss+xml': {
        'feed_path': ['rss', 'channel'],
        'entries_key': 'item'
    },
    'application/atom+xml': {
        'feed_path': ['atom:feed'],
        'entries_key': 'atom:entry'
    }
}

NAMESPACE_ALIASES = {
    'http://www.w3.org/2005/Atom': 'atom',
    'http://purl.org/dc/elements/1.1/': 'dc'
}


async def parse_xml_feed(content_type, charset, stream):
    """Parse an XML-based feed, like an RSS or Atom feed, returning a feed and
    its entries as a pair"""
    stack = [{}]

    namespace_aliases = dict(NAMESPACE_ALIASES)

    def aliased(name):
        for namespace, alias in namespace_aliases.items():
            if name.startswith(f'{{{namespace}}}'):
                return name.replace(f'{{{namespace}}}', f'{alias}:')
        return name

    xml_format = XML_FORMATS.get(content_type)

    element_stream = xml_from_stream(stream, ['start-ns', 'start', 'end'])

    async for event, element in element_stream:  # pragma no branch, bug?
        if event == 'start-ns':
            alias, namespace = element
            if namespace not in namespace_aliases:
                namespace_aliases[namespace] = alias

        elif event == 'start':
            stack.append({})

            tag = aliased(element.tag)

            # if we couldn't determine the feed format from the Content-Type,
            # guess it from the root element, or stop now
            if not xml_format:
                for xml_format in XML_FORMATS.values():
                    if tag == xml_format['feed_path'][0]:
                        break
                else:
                    raise NotImplementedError(
                        f'Unrecognized XML feed format "{content_type}"'
                    )

        else:  # event == 'end':
            child = stack.pop()

            tag = aliased(element.tag)
            attributes = dict(element.attrib)
            for attribute, value in list(attributes.items()):
                attributes[aliased(attribute)] = value

            # process text elements
            # TODO: handle Atom's type="text" and type="html"

            if 'rel' in attributes:
                child_name = f'{tag}[{attributes["rel"]}]'
            else:
                child_name = tag

            if 'href' in attributes:
                child['__value__'] = attributes['href']
            else:
                child['__value__'] = (element.text or '').strip()

            # decide what happens with the __value__

            # if the only thing in this child is a `__value__` key, just use
            # that as the child
            if set(child.keys()) == {'__value__'}:
                child = child['__value__']
            else:
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

    if not xml_format or not feed:
        return {}, []

    for step in xml_format['feed_path']:
        feed = feed[step]

    entries = feed.pop(xml_format['entries_key'])

    if not isinstance(entries, list):
        entries = [entries]

    return feed, entries
