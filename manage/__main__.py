import asyncio
import os
import sys

# from aiohttp import ClientSession, ClientTimeout


def help():
    """Prints available commands"""
    print('Usage: manage [command]')
    print()
    print('Available commands:')
    for name, function in available_commands.items():
        print('  ', name, '-', function.__doc__)


def poetry():
    os.system(' '.join(sys.argv[1:]))


def migrate():
    """Applies migrations to the database"""
    from skim.database import migrate

    asyncio.run(migrate())


def shell():
    """Opens a Python shell"""
    os.system('apython')


def dbshell():
    """Opens a SQLite3 shell to the database"""
    os.system('sqlite3 /feeds/skim.db')


def feeds():
    """Lists the current feeds"""
    from skim import subscriptions

    async def print_feeds():
        async for subscription in subscriptions.all():
            print(f"{subscription['title']}: {subscription['feed']}")

    asyncio.run(print_feeds())


def add_feed():
    """Subscribes to a new feed"""
    from skim import subscriptions

    asyncio.run(subscriptions.add(sys.argv[2]))


def remove_feed():
    """Unsubscribes from a feed"""
    from skim import subscriptions

    asyncio.run(subscriptions.remove(sys.argv[2]))


def fetch():
    from skim import crawl

    asyncio.run(crawl.fetch(sys.argv[2]))


def crawl():
    """Runs one full crawl"""
    from skim import crawl

    asyncio.run(crawl.crawl())
    asyncio.run(post_crawl_webhook())


async def post_crawl_webhook():
    webhook = os.environ.get('SKIM_POST_CRAWL_WEBHOOK')
    if not webhook:
        return

    print('Pinging webhook...')
    async with ClientSession(timeout=ClientTimeout(total=30)) as session:
        async with session.get(webhook) as response:
            print(response.status, await response.content.read())


available_commands = {
    name: function for name, function in locals().items() if callable(function)
}

try:
    command = available_commands[sys.argv[1]]
except (KeyError, IndexError):
    command = help

command()
