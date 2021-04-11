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

def dbshell():
    """Opens a SQLite3 shell to the database"""
    os.system(
        'sqlite3 /feeds/skim.db'
    )

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
