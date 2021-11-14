from bs4 import BeautifulSoup

from skim import opml


async def list_generator(items):
    for item in items:
        yield item


async def test_empty():
    subscriptions = list_generator([])
    soup = BeautifulSoup(await opml.from_subscriptions(subscriptions), 'xml')
    assert soup.opml
    assert soup.opml.head
    assert soup.opml.body
    assert not soup.opml.body.outline
    assert len(soup.select('outline')) == 0


async def test_feed_only():
    subscriptions = list_generator(
        [
            {
                'feed': 'https://example.com/xml',
            }
        ]
    )
    soup = BeautifulSoup(await opml.from_subscriptions(subscriptions), 'xml')
    assert soup.opml
    assert soup.opml.head
    assert soup.opml.body
    assert len(soup.select('opml body outline')) == 1
    for outline in soup.select('outline'):
        assert outline['title'] == 'https://example.com/xml'
        assert outline['xmlUrl'] == 'https://example.com/xml'
        assert not outline.get('htmlUrl')


async def test_with_title_and_site():
    subscriptions = list_generator(
        [
            {
                'title': 'Example',
                'site': 'https://example.com',
                'feed': 'https://example.com/xml',
            }
        ]
    )
    soup = BeautifulSoup(await opml.from_subscriptions(subscriptions), 'xml')
    assert soup.opml
    assert soup.opml.head
    assert soup.opml.body
    assert len(soup.select('opml body outline')) == 1
    for outline in soup.select('outline'):
        assert outline['title'] == 'Example'
        assert outline['htmlUrl'] == 'https://example.com'
        assert outline['xmlUrl'] == 'https://example.com/xml'
