import eventlet
eventlet.monkey_patch()

from libs.alibaba.p4p import P4P
from libs.task import Task
from flask_apscheduler import APScheduler
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_MISSED
from apscheduler.events import EVENT_JOB_ADDED
from apscheduler.events import EVENT_JOB_REMOVED
from apscheduler.events import EVENT_JOB_SUBMITTED
from apscheduler.events import EVENT_ALL

import os
from flask import Flask
from flask_socketio import SocketIO
from libs.json import JSON
from utils.eventlet_patcher import eventlet_patcher

from types import SimpleNamespace

from selenium import webdriver

import traceback
import threading
import arrow

eventlet_patcher()

socketio = SocketIO()
scheduler = APScheduler()

tasks = {}


def scheduler_listener(event):
    print(arrow.now().format('YYYY-MM-DD HH:mm:ss'), event.code)
    if event.code == EVENT_JOB_ERROR:
        print(event.exception)
        traceback.print_exc()
    elif event.code == EVENT_JOB_MISSED:
        print('EVENT_JOB_MISSED', event)
    elif event.code == EVENT_JOB_SUBMITTED:
        job = scheduler.get_job(event.job_id)
        if job:
            socketio.emit('event_task_submitted', Task(job).__dict__, namespace='/markets', broadcast=True)
    elif event.code == EVENT_JOB_ADDED:
        job = scheduler.get_job(event.job_id)
        socketio.emit('event_task_added', Task(job).__dict__, namespace='/markets', broadcast=True)
    elif event.code == EVENT_JOB_REMOVED:
        tasks[event.job_id]['is_last_run'] = True
        socketio.emit('event_task_removed', event.job_id, namespace='/markets', broadcast=True)
    elif event.code == EVENT_JOB_EXECUTED:
        job = scheduler.get_job(event.job_id)
        if job:
            socketio.emit('event_task_executed', Task(job).__dict__, namespace='/markets', broadcast=True)


def create_app(debug=True):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    scheduler.init_app(app)
    socketio.init_app(app)

    if app.debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        return app

    scheduler.add_listener(scheduler_listener, EVENT_ALL)
    scheduler.start()

    # data = dict(products=[])
    data = SimpleNamespace()

    data.reserve_title_mutex = threading.Lock()
    #
    # load products
    #
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if not markets:
        markets = {}
    data.markets = markets

    #
    # setup selenium with chrome browser
    #
    # chrome_options = webdriver.ChromeOptions()
    # # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--disable-extensions')
    # chrome_options.add_argument('--disable-logging')
    # chrome_options.add_argument('--ignore-certificate-errors')
    # data.browser = webdriver.Chrome(chrome_options=chrome_options)


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

