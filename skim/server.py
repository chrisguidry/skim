#!/usr/bin/env python
#coding: utf-8
from datetime import datetime, timedelta
import logging
import sys

from flask import Flask, abort, render_template, redirect, request, url_for
from flask.ext.assets import Environment, Bundle

from skim import logging_to_console, entries


app = Flask(__name__)
app.config.from_object('skim.configuration')

assets = Environment(app)
assets.register('stylesheets', Bundle('third-party/pure-release-0.5.0/base-min.css',
                                      'third-party/pure-release-0.5.0/grids-min.css',
                                      'third-party/pure-release-0.5.0/grids-responsive-min.css',
                                      'third-party/pygments-css/github.css',
                                      'skim.css',
                                      filters='cssmin' if not app.config['DEBUG'] else None,
                                      output='build/skim.css'))
assets.register('javascripts', Bundle('third-party/moment-2.9.0.min.js',
                                      'skim.js',
                                      filters='rjsmin' if not app.config['DEBUG'] else None,
                                      output='build/skim.js'))


@app.route('/')
def index():
    return render_template('index.html',
                           entries=entries.since(datetime.utcnow() - timedelta(hours=24)))

@app.route('/search')
def search_query():
    return render_template('index.html',
                           entries=entries.search(request.args.get('q', '')))

@app.route('/feeds')
def feed():
    return render_template('index.html',
                           entries=entries.by_feed(request.args.get('feed')))

@app.route('/interesting')
def interesting():
    return render_template('index.html',
                           entries=entries.interesting(datetime.utcnow() - timedelta(hours=72)))


if __name__ == '__main__':
    logging_to_console(logging.getLogger(''))
    bind_address, bind_port = None, None
    if len(sys.argv) == 2:
        if ':' in sys.argv[1]:
            bind_address, bind_port = sys.argv[1].split(':')
        else:
            bind_address = sys.argv[1]
    app.run(host=bind_address or '127.0.0.1', port=int(bind_port or 5000))