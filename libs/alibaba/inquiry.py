from .alibaba import Alibaba
from libs.json import JSON

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from datetime import datetime
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

import json
import requests
import time
import re
import math

import traceback
import threading

import logging
from logging.handlers import TimedRotatingFileHandler


class Inquiry:
    api = 'https://message.alibaba.com/message/default.htm'
    browser = None

    def __init__(self, market, socketio=None, namespace=None, room=None):
        self.lid = market['lid']
        self.lpwd = market['lpwd']
        self.socketio = socketio
        self.namespace = namespace
        self.room = room

    def notify(self, typo, message):
        if self.socketio:
            if '_' in typo:
                self.socketio.emit(typo, message, namespace=self.namespace, room=self.room)
            else:
                self.socketio.emit('notify', dict(type=typo, content=message), namespace=self.namespace, room=self.room)
        else:
            print(typo, message)

    def login(self):
        if self.browser is None:
            self.alibaba = Alibaba(self.lid, self.lpwd, None, None, None)
            self.alibaba.login()
            self.browser = self.alibaba.browser
        else:
            self.alibaba.login()

    def load_url(self):
        self.browser.get(self.api)
        div = self.browser.find_element_by_css_selector('div.aui-loading')
        WebDriverWait(self.browser, 15).until(EC.staleness_of(div))

    def get_inquiries(self):
        html = pq(self.browser.page_source)
        inquiry_list = html.find('.ui2-list-body .aui2-grid-wraper')
        inquiries = []
        for elem in inquiry_list:
            div = pq(elem)
            item = {}
            item['url'] = div.find('a').attr('href')
            text = div.find('div.spec-inquiry-id').text().strip()
            item['id'] = re.sub('询价单号：', '', text)
            item['date'] = div.find('div.spec-inquiry-id~div').text().strip()
            item['is_replied'] = True if div.find('td:nth-child(2) i[title="已回复"]') else False
            item['title'] = div.find('td:nth-child(3)').text()
            item['buyer'] = div.find('td:nth-child(4)').text().strip()
            item['is_buyer_online'] = True if div.find('td:nth-child(5) div.atm-online') else False
            text = div.find('td:nth-child(6) i').attr('title')
            try:
                item['buyer_country'] = re.sub(' \[.*\]', '', text)
                item['buyer_local_time'] = re.search('\[Local Time: (.*)\]', text).group(1)
            except AttributeError:
                item['buyer_country'] = text
                item['buyer_local_time'] = None
            item['responsible_person'] = div.find('td:nth-child(7)').text()
            item['status'] = div.find('td:nth-child(8)').text()
            item['status'] = div.find('td:nth-child(8)').text()
            inquiries.append(item)
        return inquiries