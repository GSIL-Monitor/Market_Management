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
    tracking_ids = None

    def __init__(self, market, socketio=None, namespace=None, room=None):
        self.market = market
        self.lid = market['lid']
        self.lpwd = market['lpwd']
        self.socketio = socketio
        self.namespace = namespace
        self.room = room
        self.load_tracking_ids()

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
        div = WebDriverWait(self.browser, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.aui-loading')))
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
            item['date'] = div.find('div.spec-inquiry-id+div').text().strip()
            item['tags'] = []
            for span in div.find('div.aui-tags span'):
                item['tags'].append(pq(span).text())
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
            if '新询盘' in item['status']:
                item['is_new'] = True
            else:
                item['is_new'] = False
            inquiries.append(item)
        return inquiries

    def get_conversation(self):
        html = pq(self.browser.page_source)
        divs = html.find('div.main-content-chat div.item-content-wrap')
        messages = []
        for elem  in divs:
            div = pq(elem)
            if div.hasClass('notification'):
                continue
            div = div.find('div.item-content')
            msg = {}
            if div.hasClass('item-content-left'):
                msg['position'] = 'left'
            elif div.hasClass('item-content-right'):
                msg['position'] = 'right'
            msg['user'] = div.find('.item-base-info span.name').text()
            msg['date'] = div.find('.item-base-info span:last-child').text()
            msg['content'] = div.find('.session-rich-content').text()
            messages.append(msg)
        buyer = {}
        email = html.find('div.main-content-sidebar div.contact-item:nth-child(2) span.contact-item-email').text()
        buyer['email'] = email
        buyer['name'] = html.find('div.main-content-sidebar div.contact-name').text()
        return { 'messages': messages, 'buyer': buyer}

    def open_inquiry_in_new_tab(self, inquiry):
        href = self.browser.find_element_by_css_selector('a[data-trade-id="' + inquiry['id'] + '"]').get_attribute(
            'href')
        self.browser.execute_script("window.open('');")
        self.browser.switch_to.window(self.browser.window_handles[1])
        self.browser.get(href)

    def close_inquiry_and_switch_back(self):
        self.browser.close()
        self.browser.switch_to_window(self.browser.window_handles[0])

    def save_tracking_ids(self):
        fn = 'inquiry_tracking_ids.json'
        root = self.market['directory'] + '_config'
        JSON.serialize(self.tracking_ids, root, [], fn)

    def load_tracking_ids(self):
        fn = 'inquiry_tracking_ids.json'
        root = self.market['directory'] + '_config'
        self.tracking_ids = JSON.deserialize(root, [], fn)
        if self.tracking_ids is None:
            self.tracking_ids = []
