import asyncio
import os
import sys

loop = asyncio.get_event_loop()


def help():
    """Prints available commands"""
    print('Usage: manage [command]')
    print()
    print('Available commands:')
    for name, function in available_commands.items():
        print('  ', name, '-', function.__doc__)


def update_requirements():
    """Updates all python requirements, saving them to requirements.txt"""
    os.system(
        'pip-compile --upgrade requirements.in --output-file requirements.txt'
    )


def migrate():
    """Applies migrations to the database"""
    from skim.migrations import migrate
    loop.run_until_complete(migrate())


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
            print(subscription['feed'])

    loop.run_until_complete(print_feeds())


def add_feed():
    """Subscribes to a new feed"""
    from skim import subscriptions
    loop.run_until_complete(subscriptions.add(sys.argv[2]))


def remove_feed():
    """Unsubscribes from a feed"""
    from skim import subscriptions
    loop.run_until_complete(subscriptions.remove(sys.argv[2]))


def fetch():
    from skim import crawl
    loop.run_until_complete(crawl.fetch(sys.argv[2]))


def crawl():
    """Runs one full crawl"""
    from skim import crawl
    loop.run_until_complete(crawl.crawl())


available_commands = {
    name: function
    for name, function in locals().items()
    if callable(function)
}

try:
    command = available_commands[sys.argv[1]]
except (KeyError, IndexError):
    command = help

command()
