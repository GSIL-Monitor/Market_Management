# -*- coding: utf-8 -*- 

from flask import session, redirect, url_for, render_template, request, make_response, current_app, send_from_directory
from . import main
from libs.json import JSON
import os

@main.route('/', methods=['GET', 'POST'])
def index():
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if markets is None:
        markets = {}
    response = make_response(render_template('index.html', markets=markets))
    return response

@main.route('/markets/<name>')
def markets(name):
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if markets is None:
        markets = {}
        market = None
    else:
        market = markets[name]

    response = make_response(render_template('markets/index.html', markets=markets, market=market))
    return response

@main.route('/p4p/<name>')
def p4p(name):
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if markets is None:
        markets = {}
    response = make_response(render_template('p4p/index.html', markets = markets))
    return response

@main.route('/settings')
def settings():
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if markets is None:
        markets = {}
    response = make_response(render_template('settings/index.html', markets = markets))
    return response

@main.route('/markets/<path:path>')
def get_file(path):
    parts = path.split('/')
    file = parts.pop()
    for key in current_app.data.markets:
        market = current_app.data.markets[key]
        if(market['name'] == parts[0]):
            parts[0]=market['directory']
    return send_from_directory(os.path.join(*parts), file, as_attachment=True)
