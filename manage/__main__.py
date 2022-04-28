import asyncio
import os
import sys

from aiohttp import ClientSession, ClientTimeout
from opentelemetry import trace

import skim
import skim.crawl
import skim.database
import skim.subscriptions


def help():  # pylint: disable=redefined-builtin
    """Prints available commands"""
    print('Usage: manage [command]')
    print()
    print('Available commands:')
    for name, function in available_commands.items():
        print('  ', name, '-', function.__doc__)


def migrate():
    """Applies migrations to the database"""
    asyncio.run(skim.database.migrate())


def shell():
    """Opens a Python shell"""
    os.system('apython')


def dbshell():
    """Opens a SQLite3 shell to the database"""
    parameters = skim.database.connection_parameters()
    os.environ['PGPASSWORD'] = parameters['password']
    os.system('psql -h {host} -p {port} -U {user} {database}'.format(**parameters))


def feeds():
    """Lists the current feeds"""

    async def print_feeds():
        async for subscription in skim.subscriptions.all_subscriptions():
            print(f"{subscription['title']}: {subscription['feed']}")

    asyncio.run(print_feeds())


def add_feed():
    """Subscribes to a new feed"""
    asyncio.run(skim.subscriptions.add(sys.argv[2]))


def remove_feed():
    """Unsubscribes from a feed"""
    asyncio.run(skim.subscriptions.remove(sys.argv[2]))


def fetch():
    asyncio.run(skim.crawl.fetch(sys.argv[2]))


def crawl():
    """Runs one full crawl"""
    asyncio.run(skim.crawl.crawl())
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
    name: function
    for name, function in locals().items()
    if callable(function) and not name.startswith('_')
}

try:
    command = available_commands[sys.argv[1]]
except (KeyError, IndexError):
    command = help

skim.configure_metrics()

tracer = trace.get_tracer('skim.manage')
with tracer.start_as_current_span(command.__name__):
    command()
