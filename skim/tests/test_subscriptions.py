from skim import subscriptions


async def test_subscriptions_management():
    before = await subscriptions.get('https://example.com')
    assert not before

    before = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' not in before

    await subscriptions.add('https://example.com')

    after = await subscriptions.get('https://example.com')
    assert after['feed'] == 'https://example.com'

    after = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' in after

    await subscriptions.remove('https://example.com')

    after = await subscriptions.get('https://example.com')
    assert not after

    after = [s['feed'] async for s in subscriptions.all()]
    assert 'https://example.com' not in after


async def test_subscriptions_updating_data():
    await subscriptions.add('https://example.com')
    await subscriptions.update(
        'https://example.com',
        title='Example!'
    )
    after = await subscriptions.get('https://example.com')
    assert after['title'] == 'Example!'
