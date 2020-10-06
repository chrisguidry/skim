import os

import aiofiles
from quart import Quart, request


app = Quart(__name__)
app.debug = (os.environ.get('DEBUG') or 'false').lower() == 'true'


@app.route('/subscriptions', methods=['GET'])
async def get_subscriptions():
    try:
        async with aiofiles.open('/feeds/subscriptions.opml', 'r') as opmlfile:
            contents = await opmlfile.read()
    except FileNotFoundError:
        contents = '<opml></opml>'

    return contents, 200, {'Content-Type': 'text/x-opml'}

@app.route('/subscriptions', methods=['PUT', 'DELETE'])
async def rewrite_subscriptions():
    async with aiofiles.open('/feeds/subscriptions.opml', 'w') as opmlfile:
        if request.method == 'DELETE':
            contents = '<opml></opml>'
        else:
            contents = await request.get_data()
            contents = contents.decode('utf-8')
        await opmlfile.write(contents)

    return await get_subscriptions()
