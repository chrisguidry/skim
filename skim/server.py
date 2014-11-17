#!/usr/bin/env python
#coding: utf-8
import sys

from flask import Flask, abort, render_template, redirect, request, url_for
from flask.ext.assets import Environment, Bundle


app = Flask(__name__)
app.config.from_object('skim.configuration')

assets = Environment(app)


@app.route('/')
def index():
    return 'hi'


if __name__ == '__main__':
    bind_address, bind_port = None, None
    if len(sys.argv) == 2:
        if ':' in sys.argv[1]:
            bind_address, bind_port = sys.argv[1].split(':')
        else:
            bind_address = sys.argv[1]
    app.run(host=bind_address or '127.0.0.1', port=int(bind_port or 5000))
