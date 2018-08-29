from celery.signals import worker_process_init,worker_init
from celery import Celery, Task, bootsteps, current_task
from celery.bin import Option
from celery.bin.worker import worker
from billiard import current_process

from libs.json import JSON
import os

from libs.alibaba.p4p import P4P
from libs.alibaba.inquiry import Inquiry
from libs.others.osoeco import OSOECO
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

import psutil
import pendulum
import arrow
import time
import re

import types
import traceback 
import threading

# app = Celery('tasks', backend='redis://localhost/0', broker='redis://localhost/0')
app = Celery('tasks')
app.config_from_object('conf.celeryconfig')

app_data = {'p4p':None, 'inquiry':None, 'browser': None}

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-software-rasterizer')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-logging')
chrome_options.add_argument('--disable-infobars')
chrome_options.add_argument('--ignore-certificate-errors')

chrome_options_headless = webdriver.ChromeOptions()
chrome_options_headless.add_argument('--headless')
chrome_options_headless.add_argument('--user-agent="' + user_agent + '"')
chrome_options_headless.add_argument('--disable-gpu')
chrome_options_headless.add_argument('--disable-software-rasterizer')
chrome_options_headless.add_argument('--disable-extensions')
chrome_options_headless.add_argument('--disable-logging')
chrome_options_headless.add_argument('--disable-infobars')
chrome_options_headless.add_argument('--ignore-certificate-errors')

@app.task(bind=True, name='tasks.p4p_record')
def p4p_record(self, group='all'):
    p4p = get_p4p(current_task.request.hostname)
    p4p.crawl(group=group)

@app.task(bind=True, name='tasks.p4p_check')
def p4p_check(self, group='all', sub_budget_limited=False):
    p4p = get_p4p(current_task.request.hostname)
    p4p.monitor(group=group, sub_budget_limited=sub_budget_limited)

@app.task(bind=True, name='tasks.set_sub_budget')
def p4p_set_sub_budget(self, sub_budget='90.00'):
    p4p = get_p4p(current_task.request.hostname)
    p4p.set_sub_budget(sub_budget)

@app.task(bind=True, name='tasks.unset_sub_budget')
def p4p_unset_sub_budget(self):
    p4p = get_p4p(current_task.request.hostname)
    p4p.unset_sub_budget()

@app.task(bind=True, name="tasks.p4p_turn_all_off")
def p4p_turn_all_off(self, group='all'):
    p4p = get_p4p(current_task.request.hostname)
    p4p.turn_all_off(group=group)

@app.task(bind=True, name="tasks.inquiry_check")
def inquiry_check(self):
    inquiry = get_inquiry(current_task.request.hostname)
    inquiry.check()

@app.task(bind=True, name="tasks.webww_check")
def webww_check(self):
    inquiry = get_inquiry(current_task.request.hostname)
    inquiry.load_url()
    inquiry.webww_check()

@app.task(bind=True, name="tasks.power_off")
def power_off(self):
    os.system('shutdown -s')

@app.task(bind=True, name="tasks.reboot")
def reboot(self):
    boot_time = pendulum.from_timestamp(psutil.boot_time(), tz='Asia/Shanghai')
    now = pendulum.now()
    if (now - boot_time).in_minutes() > 15:
        os.system("shutdown -t 180 -r -f")

@app.task(bind=True, name="tasks.osoeco_checkin")
def osoeco_checkin(self):
    if app_data['browser'] is None:
        browser = webdriver.Chrome(chrome_options=chrome_options)
        browser.set_window_size(1920, 1200)
        app_data['browser'] = browser
    OSOECO.checkin(app_data['browser'])

@app.task(bind=True, name="tasks.add")
def add(self, x, y):
    print('===>', app.conf.broker_url)
    return x+y

def get_inquiry(node):

    if app_data['inquiry'] is not None:
        return app_data['inquiry']

    text = node.split('@')[0]
    market_name = text.split(':')[0].split('[')[0]
    lname = text.split(':')[1] if len(text.split(':')) == 2 else None
    market = JSON.deserialize('.', 'storage', 'markets.json')[market_name]

    if lname is None or lname == market['lname']:
        app_data['inquiry'] = Inquiry(market, headless=False, browser=app_data['browser'])
        app_data['browser'] = app_data['inquiry'].browser
    else:
        for account in market['accounts']:
            print(lname, account)
            if lname in account['lname']:
                app_data['inquiry'] = Inquiry(market, account, headless=False, browser=app_data['browser'])
                app_data['browser'] = app_data['inquiry'].browser
    return app_data['inquiry']

def get_p4p(node):

    if app_data['p4p'] is not None:
        return app_data['p4p']

    text = node.split('@')[0]
    market_name = text.split(':')[0].split('[')[0]
    lname = text.split(':')[1] if len(text.split(':')) == 2 else None
    market = JSON.deserialize('.', 'storage', 'markets.json')[market_name]

    if lname is None or lname == market['lname']:
        lid = market['lid']
        lpwd = market['lpwd']
        lname = market['lname']
        app_data['p4p'] = P4P(market, lid, lpwd, broker_url=app.conf.broker_url, browser=app_data['browser'], headless=False)
        app_data['browser'] = app_data['p4p']
    else:
        for account in market['accounts']:
            if lname in account['lname']:
                lid = account['lid']
                lpwd = account['lpwd']
                app_data['p4p'] = P4P(market, lid, lpwd, broker_url=app.conf.broker_url, browser=app_data['browser'], headless=False)
                app_data['browser'] = app_data['p4p']

    return app_data['p4p']

def get_market():

    if app_data['p4p'] is not None:
        return app_data['p4p'].market

    global inquiry
    if app_data['inquiry'] is not None:
        return app_data['inquiry'].market

    return None
