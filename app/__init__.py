import eventlet
eventlet.monkey_patch()

import os
from flask import Flask
from flask_socketio import SocketIO
from libs.json import JSON
from utils.eventlet_patcher import eventlet_patcher

from types import SimpleNamespace
from selenium import webdriver

import threading

eventlet_patcher()
socketio = SocketIO()


def create_app(debug=True):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app)

    if app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return app


    data = SimpleNamespace()

    data.reserve_title_mutex = threading.Lock()
    #
    # load products
    #
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if not markets:
        markets = {}
    data.markets = markets


    chrome_options_headless = webdriver.ChromeOptions()
    # chrome_options_headless.add_argument('--headless')
    chrome_options_headless.add_argument('--disable-gpu')
    chrome_options_headless.add_argument('--disable-extensions')
    chrome_options_headless.add_argument('--disable-logging')
    chrome_options_headless.add_argument('--ignore-certificate-errors')
    data.chrome_options = chrome_options_headless

    data.alibaba = None
    app.data = data

    return app
