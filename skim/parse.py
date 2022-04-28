from xml.etree import ElementTree

ParseError = ElementTree.ParseError

XML_FEEDS = {
    'application/atom+xml',
    'application/rss+xml',
    'application/xml',
    'text/xml',
    'text/html',
}


async def parse(content_type, charset, stream):
    """Given the type, character set, and a stream of content, parse the feed
    and entries of the feed, yielding each as a pair."""
    if content_type in XML_FEEDS:
        return await parse_xml_feed(content_type, charset, stream)

    raise NotImplementedError(
        f'Parsing feeds of type "{content_type}" is not implemented'
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
        'entries_key': 'item',
    },
    'application/atom+xml': {
        'feed_path': ['atom:feed'],
        'entries_key': 'atom:entry',
    },
}

NAMESPACE_ALIASES = {
    'http://www.w3.org/2005/Atom': 'atom',
    'http://purl.org/dc/elements/1.1/': 'dc',
}


# Tags that are "safe" to embed unescaped in titles/descriptions
EMBEDDABLE_HTML_TAGS = {'i', 'em'}


# pylint: disable=too-many-branches
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
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
            # if there are embedded unescaped HTML tags, just capture their
            # text as in a special key called __html__ so they can be integrated
            # back as a string
            elif tag in EMBEDDABLE_HTML_TAGS:
                child_name = '__html__'
            else:
                child_name = tag

            if 'href' in attributes:
                child['__value__'] = attributes['href']
            elif tag == 'enclosure':
                child['__value__'] = attributes
            else:
                text = element.text or ''
                if tag in EMBEDDABLE_HTML_TAGS:
                    text = f'<{tag}>' + text + f'</{tag}>'
                child['__value__'] = (text + (element.tail or '')).strip()

            # decide what happens with the __value__

            # if the only thing in this child is a `__value__` key, just use
            # that as the child (possibly integration previously captured HTML)
            if set(child.keys()) == {'__value__'}:
                child = child['__value__']
            elif set(child.keys()) == {'__value__', '__html__'}:
                child = child['__value__'] + ' ' + child['__html__']
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

    feed['skim:namespaces'] = namespace_aliases

    entries = feed.pop(xml_format['entries_key'], [])

    if not isinstance(entries, list):
        entries = [entries]

    return feed, entries
