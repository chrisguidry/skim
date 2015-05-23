#!/usr/bin/env python
#coding: utf-8
from collections import defaultdict
from datetime import datetime, timedelta
from email.utils import format_datetime
import logging
import sys

from flask import Flask, abort, render_template, redirect, request, url_for
from flask.ext.assets import Environment, Bundle
from flask_debugtoolbar import DebugToolbarExtension

from skim import crawl, entries, subscriptions

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.config.from_object('skim.configuration')

app.config['DEBUG_TB_PROFILER_ENABLED'] = True
app.config['DEBUG_TB_PANELS'] = [
    'flask_debugtoolbar.panels.versions.VersionDebugPanel',
    'flask_debugtoolbar.panels.timer.TimerDebugPanel',
    'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
    'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'flask_debugtoolbar.panels.template.TemplateDebugPanel',
    'flask_debugtoolbar.panels.logger.LoggingPanel',
    'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel'
]
toolbar = DebugToolbarExtension(app)

assets = Environment(app)
assets.register('stylesheets', Bundle('third-party/pure-release-0.5.0/base-min.css',
                                      'third-party/pure-release-0.5.0/grids-min.css',
                                      'third-party/pure-release-0.5.0/grids-responsive-min.css',
                                      'third-party/pygments-css/github.css',
                                      'skim.css',
                                      filters='cssmin' if not app.config['DEBUG'] else None,
                                      output='build/skim.css'))
assets.register('javascripts', Bundle('third-party/moment-2.9.0.min.js',
                                      'third-party/list-1.1.1.min.js',
                                      'skim.js',
                                      filters='rjsmin' if not app.config['DEBUG'] else None,
                                      output='build/skim.js'))

@app.route('/')
def index():
    age = timedelta(hours=4)
    if 'older-than' in request.args:
        start = entries.datetime_from_iso(request.args['older-than'])
        start -= timedelta(microseconds=1)
    else:
        start = datetime.utcnow()

    if 'feed' in request.args:
        scope = 'feed=' + request.args.get('feed')
        results = entries.by_feed(request.args.get('feed'), start, age)
    elif 'q' in request.args:
        scope = 'q=' + request.args.get('q', '')
        results = entries.search(request.args.get('q', ''), start, age)
    else:
        scope = ''
        results = entries.older_than(start, age)

    return render_template('index.html', scope=scope, entries=results)

@app.route('/subscriptions', methods=['GET'])
def all_subscriptions():
    return render_template('subscriptions.html', subscriptions=subscriptions.subscriptions())

@app.route('/subscriptions.opml', methods=['GET'])
def opml_subscriptions():
    by_category = defaultdict(list)
    for subscription in subscriptions.subscriptions():
        if subscription.get('categories'):
            for category in subscription['categories']:
                by_category[category].append(subscription)
        else:
            by_category[''].append(subscription)
    return (render_template('subscriptions.opml',
                            by_category=by_category,
                            now_rfc822=format_datetime(datetime.utcnow())),
            200,
            {'Content-Type': 'application/xml'})

@app.route('/subscriptions', methods=['PUT'])
def subscribe():
    url = request.args.get('url')
    subscriptions.subscribe(url)
    crawl.crawl_all([url], wait=False)
    return '', 202

@app.route('/subscriptions', methods=['DELETE'])
def unsubscribe():
    url = request.args.get('url')
    subscriptions.unsubscribe(url)
    entries.remove_all_from_feed(url)
    return '', 200


if __name__ == '__main__':
    bind_address, bind_port = None, None
    if len(sys.argv) == 2:
        if ':' in sys.argv[1]:
            bind_address, bind_port = sys.argv[1].split(':')
        else:
            bind_address = sys.argv[1]
    app.run(host=bind_address or '127.0.0.1', port=int(bind_port or 5000))
