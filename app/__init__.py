import eventlet
eventlet.monkey_patch()

from libs.json import JSON
from libs.alibaba.p4p import P4P
from libs.alibaba.inquiry import Inquiry
from libs.task import Task
from flask_apscheduler import APScheduler
from apscheduler.events import EVENT_JOB_EXECUTED
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.events import EVENT_JOB_MISSED
from apscheduler.events import EVENT_JOB_ADDED
from apscheduler.events import EVENT_JOB_REMOVED
from apscheduler.events import EVENT_JOB_SUBMITTED
from apscheduler.events import EVENT_ALL

import platform
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
import time

from pywinauto.application import Application
from pywinauto.win32functions import SetForegroundWindow
import pyautogui

import logging
from logging.handlers import TimedRotatingFileHandler

eventlet_patcher()

socketio = SocketIO()
scheduler = APScheduler()

inquiries = {}
p4ps = {}
active_tasks = {}


logger = logging.getLogger('APP')
logger.setLevel(logging.DEBUG)
fh = TimedRotatingFileHandler('log/app.log', when="d", interval=1, backupCount=7)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)

app = {'current_task_id': 0}

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
        if event.job_id in active_tasks:
            active_tasks[event.job_id]['is_last_run'] = True
        socketio.emit('event_task_removed', event.job_id, namespace='/markets', broadcast=True)
    elif event.code == EVENT_JOB_EXECUTED:
        job = scheduler.get_job(event.job_id)
        if job:
            socketio.emit('event_task_executed', Task(job).__dict__, namespace='/markets', broadcast=True)


def add_task_to_scheduler_bak(market, task, room=None, power_off=False):
    tasks = []
    p4p = get_p4p(market, socketio, room)
    inquiry = get_inquiry(market)
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
        end = end_date.shift(minutes=5)
        job = scheduler._scheduler.add_job(p4p.crawl, id=task_id, trigger='interval', kwargs=kwargs, minutes=5, start_date=start.format('YYYY-MM-DD HH:mm:ss'), end_date=end.format('YYYY-MM-DD HH:mm:ss'))
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

        task_id = 'inquiry_auto_reply'
        # kwargs['tid'] = task_id
        start_date = arrow.get(task['start_date'], 'YYYY-MM-DD HH:mm:ss')
        start = start_date.shift(minutes=-2)
        end_date = arrow.get(task['end_date'], 'YYYY-MM-DD HH:mm:ss')
        end = end_date.shift(minutes=6)
        job = scheduler._scheduler.add_job(inquiry.check, id=task_id, trigger='interval', minutes=5, start_date=start.format('YYYY-MM-DD HH:mm:ss'), end_date=end.format('YYYY-MM-DD HH:mm:ss'))
        active_tasks[task_id] = {'job': job, 'is_last_run': False, 'is_running': False}
        # job.modify(next_run_time=datetime.now())
        obj = Task(job).__dict__
        obj['is_last_run'] = False
        obj['is_running'] = False
        tasks.append(obj)
    if power_off:
        task_id = 'power_off'
        off_date = arrow.get(task['end_date'], 'YYYY-MM-DD HH:mm:ss')
        off_date = off_date.shift(minutes=8)
        job = scheduler._scheduler.add_job(shutdown, id=task_id, trigger='date', run_date=off_date.format('YYYY-MM-DD HH:mm:ss'))
        active_tasks[task_id] = {'job': job, 'is_last_run': False, 'is_running': False}
        obj = Task(job).__dict__
        obj['is_last_run'] = False
        obj['is_running'] = False
        tasks.append(obj)

    return tasks

def find_next_task_id():
    app['current_task_id'] += 1
    return format(app['current_task_id'], '03d')

def schedule_task(market, task):
    tasks = []
    if task['type'] == 'monitor_and_recording':
        task['type'] = 'monitor'

        tasks.append(active_task(market, task))
        task['type'] = 'recording'
        start_date = arrow.get(task['start_date'], 'YYYY-MM-DD HH:mm:ss')
        start = start_date.shift(minutes=-3)
        task['start_date'] = start.format('YYYY-MM-DD HH:mm:ss')
        end_date = arrow.get(task['end_date'], 'YYYY-MM-DD HH:mm:ss')
        end = end_date.shift(minutes=3)
        task['end_date'] = end.format('YYYY-MM-DD HH:mm:ss')
        tasks.append(active_task(market, task))
    else:
        tasks.append(active_task(market, task))

    return tasks

def active_task(market, task):
    kwargs = {'group': task['group'], 'socketio': socketio, 'tasks': active_tasks}
    task_id = find_next_task_id()+'-'+market['name']+'-'+task['type']
    kwargs['tid'] = task_id

    if task['type'] == 'recording':
        p4p = get_p4p(market, socketio)
        job = scheduler._scheduler.add_job(p4p.crawl, id=task_id, trigger='interval', kwargs=kwargs, minutes=int(task['interval']), start_date=task['start_date'], end_date=task['end_date'])
    elif task['type'] == 'monitor':
        p4p = get_p4p(market, socketio)
        job = scheduler._scheduler.add_job(p4p.monitor, id=task_id, trigger='interval', kwargs=kwargs, minutes=int(task['interval']), start_date=task['start_date'], end_date=task['end_date'])
    elif task['type'] == 'turn_off_monitor':
        p4p = get_p4p(market, socketio)
        job = scheduler._scheduler.add_job(p4p.turn_all_off, id=task_id, trigger='date', kwargs=kwargs, run_date=task['start_date'])
    elif task['type'] == 'inquiry_reply':
        inquiry = get_inquiry(market)
        job = scheduler._scheduler.add_job(inquiry.check, id=task_id, trigger='interval', kwargs=kwargs, minutes=int(task['interval']), start_date=task['start_date'], end_date=task['end_date'])
    elif task['type'] == 'shutdown_computer':
        job = scheduler._scheduler.add_job(shutdown, id=task_id, trigger='date', run_date=task['start_date'])

    active_tasks[task_id] = {'job': job, 'is_last_run': False, 'is_running': False}
    # job.modify(next_run_time=datetime.now())
    obj = Task(job).__dict__
    obj['is_last_run'] = False
    obj['is_running'] = False
    
    return obj


def get_p4p(market, socketio, room=None):
    if market['name'] in p4ps:
        return p4ps[market['name']]
    else:
        p4p = P4P(market, market['lid'], market['lpwd'], socketio, '/markets', room)
        p4ps[market['name']] = p4p
        return p4p


def get_inquiry(market, account=None):
    lname = market['lname']
    if account is not None:
        lname = account['lname']

    key = market['name'] + lname
    if key in inquiries:
        return inquiries[key]
    else:
        inquiry = Inquiry(market, account=account)
        inquiries[key] = inquiry
        return inquiry


def shutdown():
    os.system('shutdown -s')


def run_ali_workbench(market):
    if platform.machine().endswith('64'):
        app = Application(backend="uia").start('C:\Program Files (x86)\AliWorkbench\AliWorkbench.exe --force-renderer-accessibility')
    else:
        app = Application(backend="uia").start('C:\Program Files\AliWorkbench\AliWorkbench.exe --force-renderer-accessibility')
    rect = app.dialog.rectangle()
    left = rect.left
    top = rect.top
    SetForegroundWindow(app.top_window().wrapper_object())
    x = left+434
    y = top+228
    if rect.height() == 550:
        x = left + 535
        y = top + 285
    pyautogui.moveTo(x, y)
    pyautogui.click()
    pyautogui.keyDown('ctrl')
    pyautogui.press('a')
    pyautogui.keyUp('ctrl')
    print(market['lid'])
    pyautogui.typewrite(market['lid'], interval=0.02)
    pyautogui.press('tab')
    pyautogui.keyDown('ctrl')
    pyautogui.press('a')
    pyautogui.keyUp('ctrl')
    pyautogui.press('delete')
    pyautogui.typewrite(market['lpwd'], interval=0.02)
    pyautogui.press('enter')


def start_ali_workbenchs(markets):
    delay = 180
    print(arrow.now().format('YYYY-MM-DD HH:mm:ss') + ':: alibaba workbench will start in ' + str(delay) + ' seconds.')
    time.sleep(delay)
    count = 0
    for name in markets:
        if count != 0:
            delay = 60
            print(arrow.now().format('YYYY-MM-DD HH:mm:ss') + ':: alibaba workbench will start in ' + str(
                delay) + ' seconds.')
            time.sleep(delay)
        market = markets[name]
        run_ali_workbench(market)
        count += 1


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

    thread = threading.Thread(target=start_ali_workbenchs, args=(markets,))
    # thread.start()

    for name in markets:
        now = arrow.now()
        weekday = now.weekday()
        market = markets[name]
        # run_ali_workbench(market)
        p4p_tasks = JSON.deserialize(market['directory']+"_config", '', 'p4p_tasks.json')
        if not p4p_tasks:
            p4p_tasks = []

        print()
        for task in p4p_tasks:
            if task['weekdays'][weekday]:
                t = {}
                t['interval'] = task['interval']
                # t['repeated'] = task['repeated']
                t['group'] = task['group']
                t['type'] = task['type']
                start_date = arrow.get(now.format('YYYY-MM-DD') + ' ' + task['start_date'], 'YYYY-MM-DD HH:mm:ss')
                end_date = arrow.get(now.format('YYYY-MM-DD') + ' ' + task['end_date'], 'YYYY-MM-DD HH:mm:ss')

                if end_date < start_date:
                    end_date = end_date.shift(days=1)
                if end_date < now.shift(minutes=30):
                    start_date = start_date.shift(days=1)
                    end_date = end_date.shift(days=1)
                t['start_date'] = start_date.format('YYYY-MM-DD HH:mm:ss')
                t['end_date'] = end_date.format('YYYY-MM-DD HH:mm:ss')
                print('>>>>', t)

                schedule_task(market, t)
        print()
    return app
