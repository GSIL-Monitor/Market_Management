from .alibaba import Alibaba
from libs.email import Email
from libs.json import JSON

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from string import Template
from datetime import datetime
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

import pendulum
import json
import requests
import time
import re
import os
import math
import ctypes

import traceback
import threading

import logging
from logging.handlers import TimedRotatingFileHandler


class Inquiry:
    api = 'https://message.alibaba.com/message/default.htm'
    browser = None
    tracking_ids = None
    reply_templates = {}

    def __init__(self, market, account=None, socketio=None, namespace=None, room=None):
        self.logger = logging.getLogger(market['name'])
        self.logger.setLevel(logging.DEBUG)
        fh = TimedRotatingFileHandler('log/inquiry['+market['name']+'].log', when="d", interval=1,  backupCount=7)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.market = market
        self.account = account
        self.lid = account['lid'] if account else market['lid']
        self.lpwd = account['lpwd'] if account else market['lpwd']
        self.lname = account['lname'] if account else market['lname']
        self.socketio = socketio
        self.namespace = namespace
        self.room = room

        self.account = {}
        self.account['lid'] = self.lid
        self.account['lpwd'] = self.lpwd
        self.account['lname'] = self.lname

        self.reply_js_template = "document.getElementById('tinymce').innerHTML = `{message}`;"
        self.webww_reply_js_template = "document.getElementById('tinymce').innerHTML = `{message}`;"
        self.load_tracking_ids()
        self.load_reply_templates()

        self.catalog = None
        self.load_find_catalog()

    def load_find_catalog(self):
        root = self.market['directory'] + '_config'
        for f in os.listdir(root):
            if re.search(r'[c|C]{1}atalog[ue]?.*\.pdf', f):
                self.catalog = re.sub(r'\\', '\\\\', root + '\\' + f)
                break

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
            self.alibaba = Alibaba(self.lid, self.lpwd, None, None, None, headless=False)
            self.alibaba.login()
            self.browser = self.alibaba.browser
        else:
            self.alibaba.login()

    def load_url(self):
        while True:
            try:
                if self.browser is None:
                    self.logger.info('open browser and login')
                    alibaba = Alibaba(self.lid, self.lpwd, None, None, None, headless=False)
                    alibaba.login()
                    self.browser = alibaba.browser
                    self.alibaba = alibaba

                self.browser.get(self.api)
                if 'login.alibaba.com' in self.browser.current_url:
                    self.logger.info('Was out, login again!')
                    self.alibaba.login()
                    self.browser.get(self.api)

                div = WebDriverWait(self.browser, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.aui-loading')))
                WebDriverWait(self.browser, 15).until(EC.staleness_of(div))

                # try to close all follow-me-popups
                while True:
                    btn_close = self.browser.find_elements_by_css_selector('div.follow-me-close')
                    if btn_close:
                        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
                        # wait 1 second to see if new popup commes
                        self.browser.implicitly_wait(1)
                        continue
                    else:
                        break
                break
            except WebDriverException as e:
                if 'chrome not reachable' in str(e):
                    self.logger.info('Browser Window was closed! Try to open a new browser window.')
                    self.browser = None
                continue

    def get_inquiries(self):
        html = pq(self.browser.page_source)
        inquiry_list = html.find('.ui2-list-body .aui2-grid-wraper')
        inquiries = []
        for elem in inquiry_list:
            div = pq(elem)
            item = {}
            item['url'] = div.find('a').attr('href')
            text = div.find('div.spec-inquiry-id').text().strip()
            item['id'] = re.search('(\d+)', text).group(1)
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
            if '新询盘' in item['status'] or 'New Inquiry' in item['status']:
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
        buyer['email'] = email if '@' in email else None
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
        fn = 'inquiry_tracking_ids_'+self.lname.split(' ')[0]+'.json'
        root = self.market['directory'] + '_config'
        tracking_ids = {}
        for key in self.tracking_ids:
            tracking_ids[key] = {}
            tracking_ids[key]['datetime'] = self.tracking_ids[key]['datetime'].to_atom_string()
            tracking_ids[key]['status'] = self.tracking_ids[key]['status']
            if 'emails' in self.tracking_ids[key]:
                tracking_ids[key]['emails'] = self.tracking_ids[key]['emails']
        JSON.serialize(tracking_ids, root, [], fn)

    def load_tracking_ids(self):
        fn = 'inquiry_tracking_ids_'+self.lname.split(' ')[0]+'.json'
        root = self.market['directory'] + '_config'
        tracking_ids = JSON.deserialize(root, [], fn)
        self.tracking_ids = {}
        if tracking_ids is not None:
            for key in tracking_ids:
                d = pendulum.parse(tracking_ids[key]['datetime'])
                if d.diff().in_hours()<=12:
                    self.tracking_ids[key] = {}
                    self.tracking_ids[key]['datetime'] = d
                    self.tracking_ids[key]['status'] = tracking_ids[key]['status']
                    if 'emails' in tracking_ids[key]:
                        self.tracking_ids[key]['emails'] = tracking_ids[key]['emails']

    def load_reply_templates(self):
        self.reply_templates = {}
        file = './/templates//inquiry_reply_template_acquire_email_address.html'
        with open(file, 'r') as f:
            text = f.read()
        self.reply_templates['acquire_email_address'] = Template(text)

        file = './/templates//inquiry_reply_template_notify_catalog_was_sent.html'
        with open(file, 'r') as f:
            text = f.read()
        self.reply_templates['notify_catalog_was_sent'] = Template(text)

        file = './/templates//inquiry_reply_template_first_reply_without_email.html'
        with open(file, 'r') as f:
            text = f.read()
        self.reply_templates['notify_first_reply_without_email'] = Template(text)

        file = './/templates//webww_reply_template_first_reply.html'
        with open(file, 'r') as f:
            text = f.read()
        self.reply_templates['webww_first_reply'] = Template(text)

    def is_auto_reply_needed(self, enquiry):
        eid = enquiry['id']
        #  # for testing purpose
        # if enquiry['id'] == '11947313067':
        #     self.tracking_ids[eid] = {}
        #     self.tracking_ids[eid]['datetime'] = pendulum.now()
        #     self.tracking_ids[eid]['status'] = ['new']
        #     self.save_tracking_ids()
        #     return True
        # else:
        #     return False

        if enquiry['responsible_person'].lower() != self.lname.lower():
            return False

        if eid in self.tracking_ids and self.tracking_ids[eid]['datetime'].diff().in_hours() <= 12:
            if not enquiry['is_replied']:
                return True
        if len(enquiry['tags']) == 0 and enquiry['is_new']:
            if eid not in self.tracking_ids:
                self.tracking_ids[eid] = {}
                self.tracking_ids[eid]['datetime'] = pendulum.now()
                self.tracking_ids[eid]['status'] = ['new']
                self.save_tracking_ids()
            return True
        return False

    def reply(self, enquiry):
        try:
            self.open_inquiry_in_new_tab(enquiry)
            conversation = self.get_conversation()

            messages = conversation['messages']
            buyer = conversation['buyer']

            last_buyer_messages = []
            is_replied = False
            reply_count = 0
            for msg in messages:
                if msg['position'] == 'left':
                    last_buyer_messages.append(msg)
                    is_replied = False
                elif msg['position'] == 'right' and 'Seller Assistant' not in msg['user']:
                    last_buyer_messages = []
                    is_replied = True
                    reply_count += 1

            # check if email address is already exists in conversation
            text = ''
            for msg in last_buyer_messages:
                text = text + '\n\n ' + msg['content']
            emails = re.findall('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', text)

            if buyer['email']:
                emails.append(buyer['email'])

            eid = enquiry['id']
            tracking = self.tracking_ids[eid]
            last_status = tracking['status'][-1]
            greetings = '<p>Pleased to hear from you.</p><br>'
            if last_status == 'new':
                if emails:
                    mime_message = Email.message_of_product_catalog(self.market, self.account, buyer['name'])
                    if Email.send(self.account, emails, mime_message):
                        params = {'buyer': buyer['name'], 'greetings': greetings, 'email': ','.join(emails), 'sender': self.lname}
                        message = self.reply_templates['notify_catalog_was_sent'].substitute(params)
                        if self.send_message(message, self.catalog):
                            tracking['status'].append('catalog was sent by email')
                            self.save_tracking_ids()
                        else:
                            tracking['status'].append('catalog was sent by email, but reply was failed')
                            self.save_tracking_ids()
                else:
                    params = {'buyer': buyer['name'], 'greetings': greetings, 'sender': self.lname}
                    message = self.reply_templates['notify_first_reply_without_email'].substitute(params)
                    if self.send_message(message, self.catalog):
                        tracking['status'].append('catalog was sent directly')
                        self.save_tracking_ids()
            elif 'catalog was sent' in last_status and 'reply was failed' in last_status:
                if is_replied:
                    tracking['status'].append('catalog was sent by email')
                    self.save_tracking_ids()
                else:
                    params = {'buyer': buyer['name'], 'greetings': greetings, 'email': ','.join(emails), 'sender': self.lname}
                    message = self.reply_templates['notify_catalog_was_sent'].substitute(params)
                    if self.send_message(message, self.catalog):
                        tracking['status'].append('catalog was sent by email')
                        self.save_tracking_ids()

            elif 'catalog was sent' in last_status:
                pass
            elif 'wait for email address' in last_status:
                text = ''
                for msg in last_buyer_messages:
                    text = text + '\n\n ' + msg['content']
                emails = re.findall('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', text)
                print(emails)
                if emails:
                    tracking['emails'] = emails
                    self.save_tracking_ids()
                    mime_message = Email.message_of_product_catalog(self.market, self.account, buyer['name'])
                    if Email.send(self.account, emails, mime_message):
                        params = {'buyer': buyer['name'], 'greetings': '', 'email': ', '.join(emails),
                                  'sender': self.lname}
                        message = self.reply_templates['notify_catalog_was_sent'].substitute(params)
                        if self.send_message(message, self.catalog):
                            tracking['status'].append('catalog was sent by email')
                            self.save_tracking_ids()
        except Exception as e:
            self.notify("danger", '回复 询盘 [' + enquiry['id'] + '] 时 发生错误! ' + str(e))
            traceback.print_exc()
        finally:
            self.close_inquiry_and_switch_back()

    def send_message(self, message, attach=None):
        chat_form = self.browser.find_element_by_css_selector('form.reply-wrapper')
        chat_form.click()

        uploading_failed = False
        if attach:
            file_input = self.browser.find_element_by_css_selector('input#attachs')
            file_input.send_keys(attach)

            css = 'div.next-upload-list-item:last-child'
            div = WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css)))
            try:
                WebDriverWait(self.browser, 150).until(
                    element_has_css_class(div, 'next-upload-list-item-done'))
            except TimeoutException:
                print('time out, cancel uploading')
                div.find_element_by_css_selector('i.next-icon-close').click()
                uploading_failed = True
            
        if uploading_failed:
            return False
                
        # if uploading_failed or attach is None:
        #     doc = pq(message)
        #     doc.find('span.attach').remove()
        #     message = doc.outer_html()

        WebDriverWait(self.browser, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, '#inquiry-content_ifr')))
        body = self.browser.find_element_by_tag_name('body')
        body.click()

        js = self.reply_js_template.format(message=message)
        self.browser.execute_script(js)
        self.browser.switch_to.default_content()

        time.sleep(1)

        btn_send = chat_form.find_element_by_css_selector('button.send')
        btn_send.click()
        return True

    def check(self, group=None, tid=None, socketio=None, tasks=None):
        if tid:
            tasks[tid]['is_running'] = True
            msg = {'name': 'P4P.crawl', 'tid': tid, 'group': group, 'is_last_run': tasks[tid]['is_last_run']}
            socketio.emit('event_task_start_running', msg, namespace='/markets', broadcast=True)
        if tid:
            tasks[tid]['progress'] = 1
            socketio.emit('event_task_progress', {'tid': tid, 'progress': 1}, namespace='/markets', broadcast=True)

        self.load_url()

        self.load_tracking_ids()

        if 'eyelash' in self.market['name'].lower():
            if tid:
                tasks[tid]['progress'] = 15
                socketio.emit('event_task_progress', {'tid': tid, 'progress': 15}, namespace='/markets', broadcast=True)

            time.sleep(0.1)
            inquiries = self.get_inquiries()

            if tid:
                tasks[tid]['progress'] = 20
                socketio.emit('event_task_progress', {'tid': tid, 'progress': 20}, namespace='/markets', broadcast=True)

            count = len(inquiries)

            idx = 0
            for enquiry in inquiries:
                idx += 1
                if tid:
                    progress = 20 + 80*idx/count
                    tasks[tid]['progress'] = progress
                    socketio.emit('event_task_progress', {'tid': tid, 'progress': progress}, namespace='/markets', broadcast=True)

                if not self.is_auto_reply_needed(enquiry):
                    continue

                print('enquiry ' + enquiry['id'] + ' reply is needed')
                self.reply(enquiry)
            
            if tid:
                tasks[tid]['is_running'] = False
                tasks[tid]['progress'] = 0
                if tasks[tid]['is_last_run']:
                    del tasks[tid]
                    socketio.emit('event_task_last_run_finished', {'tid': tid}, namespace='/markets', broadcast=True)

        self.webww_check()

    def webww_check(self):
        threads = []
        # try to login
        icon = WebDriverWait(self.browser, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#webatm2-iconbar')))
        container = self.browser.find_element_by_css_selector('#webww-contacts')
        dialog_iframe = self.browser.find_element_by_css_selector('#webatm2-iframe')
        while True:
            icon.click()
            WebDriverWait(self.browser, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, '#webww-contacts .webatm2-tips')))
            confirm = self.browser.find_element_by_css_selector('#webww-contacts .webatm2-confirm')
            if confirm.is_displayed():
                # failed login, cancel checking
                print('Trade Manager has been loged in somewhere else, cancel checking')
                close_btn = confirm.find_element_by_css_selector('span.webatm2-confirm-close')
                close_btn.click()
                return threads

            if 'show-panel' in container.get_attribute('class'):
                break

        panel = WebDriverWait(self.browser, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#webatm2-panel')))
        # after login

        # open dialog
        #     tab_recent = panel.find_element_by_css_selector('div.tab-recent')
        #     if 'unread' not in tab_recent.get_attribute('class'):
        #         print('there is no new messages.')
        #         return threads

        tab_sysmsg = panel.find_element_by_css_selector('div.tab-sysmsg')
        tab_sysmsg.click()
        panel.find_element_by_css_selector('.panel-sysmsg.active a').click()
        WebDriverWait(self.browser, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#webatm2-dialog')))

        # switch to iframe and navigate to recent threads
        self.browser.switch_to.frame(dialog_iframe)
        sidebar = self.browser.find_element_by_css_selector('.webatm2-sidebar')
        head = self.browser.find_element_by_css_selector('.webatm2-window-head')
        body = self.browser.find_element_by_css_selector('.webatm2-window-body')
        sidebar.find_element_by_css_selector('.tab-thread').click()
        time.sleep(1)
        doc = pq(sidebar.find_element_by_css_selector('.webatm2-thread-list').get_attribute('innerHTML'))
        for div in doc.find('.webatm2-thread'):
            div = pq(div)
            thread = {}
            thread['id'] = div.attr('data-user-id')
            thread['online'] = not div.hasClass('offline')
            thread['name'] = div.find('.thread-info .name').text()
            thread['unread'] = div.hasClass('unread')
            thread['unread_count'] = int(div.find('.thread-info span.unread').text())
            threads.append(thread)

            if thread['unread_count'] == 0:
                continue

            if re.search('[\u4E00-\u9FA5]+', thread['name']):  # old thread
                continue

            tid = thread['id']
            if tid not in self.tracking_ids:
                self.tracking_ids[tid] = {}
                self.tracking_ids[tid]['datetime'] = pendulum.now()
                self.tracking_ids[tid]['status'] = ['new']
                self.save_tracking_ids()
            self.webww_switch_to_thread(thread, sidebar, head, body)

        self.browser.switch_to.default_content()
        return threads

    def webww_switch_to_thread(self, thread, sidebar, head, body):

        div = sidebar.find_element_by_css_selector('div.webatm2-thread[data-user-id="' + thread['id'] + '"]')

        if 'active' not in div.get_attribute('class'):
            # msgs = body.find_elements_by_css_selector('.webatm2-messages .webatm2-message')
            div.click()

        #     if msgs:
        #         print(msgs)
        #         WebDriverWait(self.browser, 15).until(EC.staleness_of(msgs[-1]))
        #     else:
        #         WebDriverWait(self.browser, 15).until(
        #             EC.presence_of_element_located((By.CSS_SELECTOR, '.webatm2-messages .webatm2-message')))
        #     time.sleep(1)
        # WebDriverWait(self.browser, 15).until(
        #     EC.text_to_be_present_in_element((By.CSS_SELECTOR, '.webatm2-window-head .user-name'), thread['name']))

        WebDriverWait(self.browser, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, '.show-contact iframe')))
        buyer_name = ''
        country = ''
        login_location = ''
        is_Alibaba_employee = False
        try:
            buyer_name = self.browser.find_element_by_css_selector('#mini-card-wrap span.user-nick').text
            span_country = self.browser.find_element_by_css_selector(
                '#mini-card-wrap .user-base-info-wrap span:nth-child(2)')
            country = re.search(':(.*)', span_country.get_attribute('title')).group(1)

            spans = self.browser.find_elements_by_css_selector('#vaildEmployee')
            if spans:
                is_Alibaba_employee = True

            p_login_location = self.browser.find_elements_by_css_selector('#mini-card-wrap p.last-login-time')
            if p_login_location:
                login_location = re.search(':(.*)', p_login_location[0].get_attribute('title')).group(1)
        except Exception as e:
            traceback.print_exc()
        finally:
            self.browser.switch_to.parent_frame()

        print(buyer_name, is_Alibaba_employee, country, login_location)
        doc = pq(self.browser.find_element_by_css_selector('.webatm2-window-body .webatm2-messages').get_attribute(
            'innerHTML'))

        is_replied = False
        last_buyer_message = []
        messages = []
        for div in doc.find('.webatm2-message'):
            div = pq(div)
            message = {}
            message['is_self'] = div.hasClass('self')
            message['datetime'] = div.find('.time-tag').text() if div.find('.time-tag') else None
            message['content'] = div.find('.content').text().replace('\xa0', ' ')

            if message['is_self']:
                last_buyer_message = []
                is_replied = True
            else:
                last_buyer_message.append(message)
                is_replied = False

            messages.append(message)

        tid = thread['id']
        tracking = self.tracking_ids[tid]
        last_status = tracking['status'][-1]
        if is_replied:
            pass
        elif is_Alibaba_employee:
            msg = '0123456789'
            self.webww_send_message(msg, body)
            tracking['status'].append('irrelevant reply')
            self.save_tracking_ids()
        elif last_status == 'new':
            link = 'https://drive.google.com/file/d/1gfHwDl1qPomAMnkFGCjiVk74e8CQagoI'
            salutation = 'hi'
            if buyer_name:
                salutation = 'Dear ' + buyer_name
            params = {'salutation': salutation, 'link': link, 'sender': self.lname}
            msg = inquiry.reply_templates['webww_first_reply'].substitute(params)
            self.webww_send_message(msg, body)
            tracking['status'].append('link to catalog was send directly')
            self.save_tracking_ids()
        elif 'link to catalog was send' in last_status:
            pass
        else:
            pass

    def webww_send_message(self, msg, body):
        edit = body.find_element_by_css_selector('div.webatm2-editor-body')
        for part in msg.split('\n'):
            edit.send_keys(part)
            print(part)
            ActionChains(self.browser).key_down(Keys.SHIFT).key_down(Keys.ENTER).key_up(Keys.SHIFT).perform()
        edit.send_keys(Keys.BACKSPACE)
        send_btn = body.find_element_by_css_selector('button.send')
        # send_btn.click()

class element_has_css_class(object):
    def __init__(self, element, css_class):
        self.element = element
        self.css_class = css_class

    def __call__(self, driver):
        if self.css_class in self.element.get_attribute("class"):
            return self.element
        else:
            return False
