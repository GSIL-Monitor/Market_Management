from libs.alibaba.alibaba import Alibaba

from libs.json import JSON

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.select import Select
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq
from libs.CeleryTasks import tasks
import html
import time
import re
import os
import traceback
import types
import pendulum


class Visitor:
    api = 'http://hz-mydata.alibaba.com/self/visitors.htm'
    browser = None

    def __init__(self, market, headless=True, browser=None):
        self.market = market
        self.lid = market['lid']
        self.lpwd = market['lpwd']

        self.confi_dir = market['directory'] + '_config'
        self.visitor_dir = self.confi_dir + '//'+'visitors'

        self.alibaba = None
        self.browser = browser
        self.headless = headless

        self.products = {}
        root = market['directory']+'_config'
        product_list = JSON.deserialize(root, '.', 'product_list.json')
        for p in product_list:
            self.products[p['ali_id']] = p

        rp = {}
        rp['mink eyelash'] = {'ali_id': '60761530720', 'price': 1.5}
        rp['silk eyelash'] = {'ali_id': '60795757606', 'price': 0.8}
        rp['magnetic eyelash'] = {'ali_id': '60763607812', 'price': 1.1}
        rp['individual eyelash'] = {'ali_id': '60732345735', 'price': 2.3}
        rp['premade fans glue bonded'] = {'ali_id': '60762376749', 'price': 1.6}
        rp['premade fans heat bonded'] = {'ali_id': '60795873604', 'price': 1.9}

        self.recommended = {}
        self.recommended['mink'] = [rp['mink eyelash'], rp['silk eyelash'], rp['magnetic eyelash']]
        self.recommended['silk'] = [rp['silk eyelash'], rp['mink eyelash'], rp['magnetic eyelash']]
        self.recommended['magnetic'] = [rp['magnetic eyelash'], rp['mink eyelash'], rp['silk eyelash']]
        self.recommended['individual eyelash'] = [rp['individual eyelash'], rp['premade fans glue bonded'], rp['premade fans heat bonded']]
        self.recommended['glue bonded'] = [rp['premade fans glue bonded'], rp['premade fans heat bonded'], rp['individual eyelash']]
        self.recommended['heat bonded'] = [rp['premade fans heat bonded'], rp['premade fans glue bonded'], rp['individual eyelash']]
        self.recommended['premade fans'] = self.recommended['glue bonded']
        self.recommended['default'] = self.recommended['mink'] + self.recommended['individual eyelash']

        self.mail_message = "Hi,\\nNice Day. This is Ada.\\nThanks for your visit to our products.\\nWould you pls tell us your WhatsApp number? I would like to send our product catalog and price list to you. Thanks\\nMy WhatsApp  is +8618563918130.\\n\\nRegards\\nAda"

    def login(self):
        self.alibaba = Alibaba(self.lid, self.lpwd, headless=self.headless, browser=self.browser)
        self.alibaba.login()
        self.browser = self.alibaba.browser

    def load_url(self):
        while True:
            try:
                if self.alibaba is None:
                    alibaba = Alibaba(self.lid, self.lpwd, headless=self.headless, browser=self.browser)
                    alibaba.login()
                    if self.browser is None:
                        self.browser = alibaba.browser
                    self.alibaba = alibaba

                self.browser.get(self.api)
                if 'login.alibaba.com' in self.browser.current_url:
                    self.alibaba.login()
                    self.browser.get(self.api)

                WebDriverWait(self.browser, 15).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))

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
                    print(str(e))
                    self.browser = None
                continue

    def parse_tr(self, tr):
        visitor = {}
        date = tr.find_element_by_css_selector('td.td-checkbox input').get_attribute('statdate')
        visitor['id'] = tr.find_element_by_css_selector('td.td-checkbox input').get_attribute('visitorid')
        visitor['idx'] = tr.find_element_by_css_selector('td.td-checkbox input').get_attribute('visitoridx')
        visitor['date'] = date
        visitor['region'] = tr.find_element_by_css_selector('td.td-region span').get_attribute('title')

        pv_span = tr.find_element_by_css_selector('td.td-pv span')
        visitor['pv'] = pv_span.text

        visitor['pv-detail'] = []
        if visitor['pv'] != '0':
            css_pv_detail = '#J-visitor-detail'
            css_pv_detail_close = '#J-vistor-detail-close'
            css_pv_detail_body = '#J-visitor-detail-tbl-tbody'
            css_pv_detail_pagination = '#J-pagination-visitor-detail'
            pv_span.click()
            while True:
                pv_detail_tbody = WebDriverWait(self.browser, 15).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, css_pv_detail_body)))

                for pv_tr in pv_detail_tbody.find_elements_by_css_selector('tr'):
                    pv = {}
                    pv['idx'] = pv_tr.find_element_by_css_selector('td.visitor-detail-index').text
                    pv['page'] = pv_tr.find_element_by_css_selector('td.visitor-detail-page a').get_attribute('href')
                    page_acts = pv_tr.find_element_by_css_selector('td.visitor-detail-page div').text
                    if '已发起询盘' in page_acts:
                        pv['inquiried'] = True
                    else:
                        pv['inquiried'] = False

                    if '已发起TradeManager咨询' in page_acts:
                        pv['tm_inquiried'] = True
                    else:
                        pv['tm_inquiried'] = False
                    pv['stay'] = pv_tr.find_element_by_css_selector('td.visitor-detail-stay').text
                    pv['time'] = pv_tr.find_element_by_css_selector('td.visitor-detail-time').text
                    visitor['pv-detail'].append(pv)

                next_pv_detail_button = self.browser.find_elements_by_css_selector(css_pv_detail_pagination + ' .ui-pagination-active + a')
                if next_pv_detail_button:
                    while True:
                        try:
                            ActionChains(self.browser).move_to_element(next_pv_detail_button[0]).perform()
                            next_pv_detail_button[0].click()
                            break
                        except WebDriverException as e:
                            if 'is not clickable at point' in str(e):
                                self.browser.implicitly_wait(0.5)
                                continue
                            else:
                                raise e
                else:
                    break

            while True:
                try:
                    self.browser.find_element_by_css_selector(css_pv_detail_close).click()
                    break
                except WebDriverException as e:
                    if 'is not clickable at point' in str(e):
                        self.browser.implicitly_wait(0.5)
                        continue
                    else:
                        raise e

        visitor['stay'] = tr.find_element_by_css_selector('td.td-stay-duration').text

        kws_div = tr.find_elements_by_css_selector('td.td-search-keywords>div.search-keywords')
        if kws_div:
            kws_div = kws_div[0]
            kws_text = kws_div.get_attribute('data-text')
            visitor['keywords'] =  re.sub('</div><div>', ',', kws_text)[5:-6].split(',')
            visitor['search_keyword_indices'] = []
            for idx, div in enumerate(kws_div.find_elements_by_css_selector('div')):
                if div.find_elements_by_css_selector('span.search-keyword'):
                    visitor['search_keyword_indices'].append(idx)
        else:
            visitor['keywords'] = []
            visitor['search_keyword_indices'] = []

        visitor['minisite-acts'] = []
        for div in tr.find_elements_by_css_selector('td.td-minisite-active span'):
            visitor['minisite-acts'].append(div.get_attribute('textContent'))
        visitor['website-acts'] = []
        for div in tr.find_elements_by_css_selector('td.td-website-active span'):
            visitor['website-acts'].append(div.get_attribute('textContent'))

        return visitor

    def crawl_current_page_visitors(self):
        css_tbody = '#J-visitors-tbl-tbody'
        tbody = WebDriverWait(self.browser, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_tbody)))

        visitors = []
        fns = os.listdir(self.visitor_dir)

        for tr in tbody.find_elements_by_css_selector(css_tbody+' tr.J-visitors-table-tr'):
            ActionChains(self.browser).move_to_element(tr).perform()

            visitor = self.parse_tr(tr)

            fn = 'visitors_'+visitor['date']+'.json'
            if fn in fns:
                break

            visitors.append(visitor)

        return visitors

    def switch_to_last_31_days(self):
        css_date = '#J-common-state-date'
        css_option = '#J-common-state-options'
        
        date = self.browser.find_element_by_css_selector(css_date)
        date.click()
        
        option = WebDriverWait(self.browser, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_option)))
        option.find_element_by_css_selector('li[data-option="31"]').click()

    def next_page(self):
        css_next_page_button = '#J-pagination-visitors .ui-pagination-active+a'
        next_page_button = self.browser.find_elements_by_css_selector(css_next_page_button)
        if next_page_button:
            ActionChains(self.browser).move_to_element(next_page_button[0]).perform()
            next_page_button[0].click()
            return True
        else:
            return False

    def crawl_visitors(self):
        visitors = []
        while True:
            result = self.crawl_current_page_visitors()
            if result:
                visitors += result
            if not result or not self.next_page():
                break
        return visitors

    def serialize(self, visitors):
        dates = {}
        for v in visitors:
            date = v['date']
            if date not in dates:
                dates[date] = []
            dates[date].append(v)

        for d in dates:
            fn = 'visitors_'+d+'.json'
            JSON.serialize(dates[d], self.confi_dir, 'visitors', fn)

    def deserialize(self):
        files = os.listdir(self.visitor_dir)
        visitors = []
        for f in files:
            if not f.startswith('visitors_') or not f.endswith('.json'):
                continue
            visitors += JSON.deserialize(self.confi_dir, 'visitors', f)
        return visitors

    def update(self):
        self.load_url()
        close_btn = self.browser.find_elements_by_css_selector('div.ui-window a.ui-window-close')
        if close_btn and close_btn[0].is_displayed():
            close_btn[0].click()
        self.switch_to_last_31_days()
        visitors = self.crawl_visitors()
        self.serialize(visitors)

    def mail(self):
        self.load_url()
        close_btn = self.browser.find_elements_by_css_selector('div.ui-window a.ui-window-close')
        if close_btn and close_btn[0].is_displayed():
            close_btn[0].click()
        self.switch_to_last_31_days()

        check_box = self.browser.find_elements_by_css_selector('input#J-condition-mailable')
        if check_box:
            check_box[0].click()
            
        while True:
            result = self.mail_to_current_page_visitors()

            if not self.next_page():
                break

    def mail_to_current_page_visitors(self):
        pass

    def mail_to_visitor(self, tr, recommendation):
        pass