import aiofiles
import aiofiles.os
from aiohttp import web

routes = web.RouteTableDef()


@routes.get('/subscriptions')
async def get_subscriptions(request):
    try:
        async with aiofiles.open('/feeds/subscriptions.opml', 'r') as opmlfile:
            contents = await opmlfile.read()
    except FileNotFoundError:
        contents = '<opml></opml>'

    return web.Response(text=contents, content_type='text/x-opml')


@routes.put('/subscriptions')
async def set_subscriptions(request):
    async with aiofiles.open('/feeds/subscriptions.opml', 'w') as opmlfile:
        contents = await request.text()
        await opmlfile.write(contents)

    return await get_subscriptions(request)


@routes.delete('/subscriptions')
async def delete_subscriptions(request):
    try:
        await aiofiles.os.remove('/feeds/subscriptions.opml')
    except FileNotFoundError:
        pass

    return web.Response(text='', status=204)