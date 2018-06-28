import eventlet
eventlet.monkey_patch()

from libs.json import JSON
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

import logging
from logging.handlers import TimedRotatingFileHandler

eventlet_patcher()

socketio = SocketIO()
scheduler = APScheduler()

p4ps = {}
active_tasks = {}

logger = logging.getLogger('APP')
logger.setLevel(logging.DEBUG)
fh = TimedRotatingFileHandler('log/app.log', when="d", interval=1, backupCount=7)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)


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
        if event.job_id in tasks:
            tasks[event.job_id]['is_last_run'] = True
        socketio.emit('event_task_removed', event.job_id, namespace='/markets', broadcast=True)
    elif event.code == EVENT_JOB_EXECUTED:
        job = scheduler.get_job(event.job_id)
        if job:
            socketio.emit('event_task_executed', Task(job).__dict__, namespace='/markets', broadcast=True)


def schedule_task(market, task, room=None):
    tasks = []
    p4p = get_p4p(market, socketio, room)
    kwargs = {'group': task['group'], 'socketio': socketio, 'tasks': active_tasks}
    if task['type'] == 'recording':
        task_id = find_next_task_id(task_type='recording')
        kwargs['tid'] = task_id
        job = scheduler._scheduler.add_job(p4p.crawl, id=task_id, trigger='interval', kwargs=kwargs, minutes=int(task['interval']), start_date=task['start_date'], end_date=task['end_date'])
        active_tasks[task_id] = {'job': job, 'is_last_run': False, 'is_running': False}
        # job.modify(next_run_time=datetime.now())
        obj = Task(job).__dict__
        obj['is_last_run'] = False
        obj['is_running'] = False
        tasks.append(obj)
    elif task['type'] == 'monitor':
        task_id = find_next_task_id(task_type='recording')
        kwargs['tid'] = task_id
        start_date = arrow.get(task['start_date'], 'YYYY-MM-DD HH:mm:ss')
        start = start_date.shift(minutes=-3)
        end_date = arrow.get(task['end_date'], 'YYYY-MM-DD HH:mm:ss')
        end = end_date.shift(minutes=3)
        job = scheduler._scheduler.add_job(p4p.crawl, id=task_id, trigger='interval', kwargs=kwargs, minutes=int(task['interval']), start_date=start.format('YYYY-MM-DD HH:mm:ss'), end_date=end.format('YYYY-MM-DD HH:mm:ss'))
        active_tasks[task_id] = {'job': job, 'is_last_run': False, 'is_running': False}
        # job.modify(next_run_time=datetime.now())
        obj = Task(job).__dict__
        obj['is_last_run'] = False
        obj['is_running'] = False
        tasks.append(obj)

        task_id = find_next_task_id(task_type='monitor')
        kwargs['tid'] = task_id
        job = scheduler._scheduler.add_job(p4p.monitor, id=task_id, trigger='interval', kwargs=kwargs, minutes=int(task['interval']), start_date=task['start_date'], end_date=task['end_date'])
        active_tasks[task_id] = {'job': job, 'is_last_run': False, 'is_running': False}
        # job.modify(next_run_time=datetime.now())
        obj = Task(job).__dict__
        obj['is_last_run'] = False
        obj['is_running'] = False
        tasks.append(obj)

        task_id = find_next_task_id(task_type='monitor')
        kwargs['tid'] = task_id
        run_date = arrow.get(task['end_date'], 'YYYY-MM-DD HH:mm:ss')
        run_date = run_date.shift(minutes=2)
        job = scheduler._scheduler.add_job(p4p.turn_all_off, id=task_id, trigger='date', kwargs=kwargs, run_date=run_date.format('YYYY-MM-DD HH:mm:ss'))
        active_tasks[task_id] = {'job': job, 'is_last_run': False, 'is_running': False}
        obj = Task(job).__dict__
        obj['is_last_run'] = False
        obj['is_running'] = False
        tasks.append(obj)


def find_next_task_id(task_type='recording'):
    max_tid = 0
    # jobs = scheduler.get_jobs()
    for id in active_tasks:
        text = id
        if task_type in text:
            tid = int(text.split('_')[1])
            if tid > max_tid:
                max_tid = tid
    max_tid += 1
    return task_type + '_' + str(max_tid)


def get_p4p(market, socketio, room=None):
    if market['name'] in p4ps:
        return p4ps[market['name']]
    else:
        p4p = P4P(market, market['lid'], market['lpwd'], socketio, '/markets', room)
        p4ps[market['name']] = p4p
        return p4p


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

    logger.info('app begin to start ... ... ')

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

    markets = JSON.deserialize('.', 'storage', 'markets.json')
    for name in markets:
        now = arrow.now()
        weekday = now.weekday()
        market = markets[name]
        p4p_tasks = JSON.deserialize(market['directory']+"_config", '', 'p4p_tasks.json')
        for task in p4p_tasks:
            if task['weekdays'][weekday]:
                t = {}
                t['interval'] = task['interval']
                t['group'] = task['group']
                t['type'] = task['type']
                start_date = arrow.get(now.format('YYYY-MM-DD') + ' ' + task['start_date'], 'YYYY-MM-DD HH:mm:ss')
                end_date = arrow.get(now.format('YYYY-MM-DD') + ' ' + task['end_date'], 'YYYY-MM-DD HH:mm:ss')
                if end_date < start_date:
                    end_date = end_date.shift(days=1)
                t['start_date'] = start_date.format('YYYY-MM-DD HH:mm:ss')
                t['end_date'] = end_date.format('YYYY-MM-DD HH:mm:ss')
                schedule_task(market, t)

    logger.info("app is now ready for accessing")
    return app

