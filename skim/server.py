#!/usr/bin/env python
#coding: utf-8
from datetime import datetime, timedelta
import os
import os.path
import sys

from flask import Flask, abort, render_template, redirect, request, url_for
from flask.ext.assets import Environment, Bundle

from skim.configuration import STORAGE_ROOT
from skim.entries import entry_filenames_by_time, full_entry
from skim.search import search

app = Flask(__name__)
app.config.from_object('skim.configuration')

assets = Environment(app)
assets.register('stylesheets', Bundle('third-party/pure-release-0.5.0/base-min.css',
                                      'third-party/pure-release-0.5.0/grids-min.css',
                                      'third-party/pure-release-0.5.0/grids-responsive-min.css',
                                      'skim.css',
                                      filters='cssmin' if not app.config['DEBUG'] else None,
                                      output='build/skim.css'))
assets.register('javascripts', Bundle('skim.js',
                                      filters='rjsmin' if not app.config['DEBUG'] else None,
                                      output='build/skim.js'))

@app.route('/')
def index():
    entry_filenames = entry_filenames_by_time(datetime.utcnow() - timedelta(hours=4))
    all_entries = [full_entry(filename) for filename in entry_filenames]
    context = {
        'long_entries': [entry for entry in all_entries if len(entry['body']) > 1000],
        'short_entries': [entry for entry in all_entries if len(entry['body']) <= 1000]
    }
    return render_template('index.html', **context)

@app.route('/search')
def search_query():
    results = search(request.args.get('q', ''))
    entry_filenames = [os.path.join(STORAGE_ROOT, result['path']) for result in results]
    all_entries = [full_entry(filename) for filename in entry_filenames]
    context = {
        'long_entries': [entry for entry in all_entries if len(entry['body']) > 1000],
        'short_entries': [entry for entry in all_entries if len(entry['body']) <= 1000]
    }
    return render_template('index.html', **context)

if __name__ == '__main__':
    bind_address, bind_port = None, None
    if len(sys.argv) == 2:
        if ':' in sys.argv[1]:
            bind_address, bind_port = sys.argv[1].split(':')
        else:
            bind_address = sys.argv[1]
    app.run(host=bind_address or '127.0.0.1', port=int(bind_port or 5000))
