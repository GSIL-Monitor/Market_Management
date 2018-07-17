from celery.signals import worker_process_init,worker_init
from celery import Celery, Task, bootsteps, current_task
from celery.bin import Option
from celery.bin.worker import worker
from billiard import current_process

from libs.json import JSON
import os

from libs.alibaba.p4p import P4P
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

@app.task(bind=True)
def p4p_check(self, group='all'):
    global p4p
    if p4p is None:
        node = current_task.request.hostname
        p4p = get_p4p(node)

    p4p.crawl(group=group)

@app.task(bind=True)
def p4p_turn_all_off(self, group='all'):
    global p4p
    if p4p is None:
        node = current_task.request.hostname
        p4p = get_p4p(node)

    p4p.turn_all_off(group=group)

@app.task(bind=True, ignore_result=True)
def p4p_info(self):
    return p4p.market if p4p else 'not initialized yet!'

def get_p4p(node):
    text = node.split('@')[0]
    market_name = text.split(':')[0]
    lname = text.split(':')[1] if len(text.split(':')) == 2 else None
    market = JSON.deserialize('.', 'storage', 'markets.json')[market_name]

    if lname is None or lname == market['lname']:
        lid = market['lid']
        lpwd = market['lpwd']
        lname = market['lname']
    else:
        for account in market['accounts']:
            lid = account['lid']
            lpwd = account['lpwd']
            lname = account['lname']
    return P4P(market, lid, lpwd)