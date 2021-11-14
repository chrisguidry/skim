from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement


async def from_subscriptions(subscriptions):
    opml = Element('opml', attrib={'version': '2.0'})
    SubElement(opml, 'head')
    body = SubElement(opml, 'body')

    async for subscription in subscriptions:  # pragma no branch, bug?
        attributes = {
            'title': (
                subscription.get('title')
                or subscription.get('site')
                or subscription['feed']
            ),
            'xmlUrl': subscription['feed'],
        }
        if subscription.get('site'):
            attributes['htmlUrl'] = subscription['site']

        SubElement(body, 'outline', attrib=attributes)

    ElementTree.indent(opml)
    return ElementTree.tostring(opml, encoding='unicode')
