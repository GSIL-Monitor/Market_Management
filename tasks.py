from celery.signals import worker_process_init,worker_init
from celery import Celery, Task, bootsteps, current_task
from celery.bin import Option
from celery.bin.worker import worker
from billiard import current_process

from libs.json import JSON
import os

from libs.alibaba.p4p import P4P
from libs.alibaba.inquiry import Inquiry
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

import pendulum
import arrow
import imp
import time
import re

import types
import traceback 
import threading

# app = Celery('tasks', backend='redis://localhost/0', broker='redis://localhost/0')
app = Celery('tasks')
app.config_from_object('celeryconfig')

p4p = None
inquiry = None

@app.task(bind=True)
def p4p_check(self, group='all'):
    p4p = get_p4p(current_task.request.hostname)
    p4p.monitor(group=group)

@app.task(bind=True)
def p4p_turn_all_off(self, group='all'):
    p4p = get_p4p(current_task.request.hostname)
    p4p.turn_all_off(group=group)

@app.task(bind=True)
def inquiry_check(self):
    inquiry = get_inquiry(current_task.request.hostname)
    inquiry.check()

@app.task(bind=True, ignore_result=True)
def p4p_info(self):
    return p4p.market if p4p else 'not initialized yet!'

@app.task(bind=True)
def power_off(self):
    os.system('shutdown -s')
    pass

def get_inquiry(node):
    global inquiry
    if inquiry is not None:
        return inquiry

    text = node.split('@')[0]
    market_name = text.split(':')[0].split('<')[0]
    lname = text.split(':')[1] if len(text.split(':')) == 2 else None
    market = JSON.deserialize('.', 'storage', 'markets.json')[market_name]

    if lname is None or lname == market['lname']:
        inquiry = Inquiry(market)
    else:
        for account in market['accounts']:
            if lname == account['lname']:
                inquiry = P4P(market, account)
    return inquiry

def get_p4p(node):
    global p4p
    if p4p is not None:
        return p4p

    text = node.split('@')[0]
    market_name = text.split(':')[0].split('<')[0]
    lname = text.split(':')[1] if len(text.split(':')) == 2 else None
    market = JSON.deserialize('.', 'storage', 'markets.json')[market_name]

    if lname is None or lname == market['lname']:
        lid = market['lid']
        lpwd = market['lpwd']
        lname = market['lname']
        p4p = P4P(market, lid, lpwd)
    else:
        for account in market['accounts']:
            if lname == account['lname']:
                lid = account['lid']
                lpwd = account['lpwd']
                p4p = P4P(market, lid, lpwd)
    return p4p
