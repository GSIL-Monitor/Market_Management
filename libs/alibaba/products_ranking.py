from libs.alibaba.alibaba import Alibaba
from libs.alibaba.p4p import P4P
from libs.json import JSON

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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from datetime import datetime
from bs4 import BeautifulSoup
from pyquery import PyQuery as pq

import json
import requests
import redis
import pendulum
import arrow
import imp
import time
import re

import types
import traceback 
import threading

class ProductsRanking:
    chrome_options = webdriver.ChromeOptions()

    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"}
    api = 'https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&viewtype=G&CatId=&SearchText='
    current_page = 0
    
    market = None
    
    def __init__(self, market=None):
        self.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        self.headers['Accept-Encoding'] = 'gzip, deflate, br'
        self.headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'
        self.headers['cache-control'] = 'no-cache'
        self.headers['Connection'] = 'Keep-Alive'
        self.headers['Connection'] = 'close'
        self.headers['Host'] = 'www.alibaba.com'
        self.headers['Upgrade-Insecure-Requests'] = '1'
        
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-software-rasterizer')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument('--disable-logging')
        self.chrome_options.add_argument('--disable-infobars')
        self.chrome_options.add_argument('--ignore-certificate-errors')
        prefs = {"profile.managed_default_content_settings.images": 2}
        self.chrome_options.add_experimental_option("prefs", prefs)
#         self.chrome_options.add_argument('--headless')
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
        self.chrome_options.add_argument('--user-agent="'+user_agent+'"')
        
        self.open_browser()
        self.get('https://www.alibaba.com')
        
        self.market = market
        
    def open_browser(self):
        caps = DesiredCapabilities().CHROME
#         caps["pageLoadStrategy"] = "normal"  #  complete
#         caps["pageLoadStrategy"] = "eager"  #  interactive
        caps["pageLoadStrategy"] = "none"
        self.browser = webdriver.Chrome(chrome_options=self.chrome_options, desired_capabilities=caps)
        
        
    def crawl_current_page(self, html, records=[]):
        
        for idx, item in enumerate(pq(html).find('div.item-main')):
            record = {}
            item = pq(item)
            
            record['location'] = {}
            record['location']['page'] = self.current_page
            record['location']['position'] = idx+1
            
            if item.find('h2.title i.ui2-icon-crown'):
                record['is_top_sponsor'] = True
            else:
                record['is_top_sponsor'] = False

            if item.find('h2.title div.sl'):
                record['is_sponsor'] = True
            else:
                record['is_sponsor'] = False
            
            product = {}
            record['product'] = product
            product['id'] = item.parent().attr('data-ctrdot')
            a = item.find('h2.title a')
            product['title'] = a.attr('title')
            product['href'] = a.attr('href')
            product['img'] = item.find('div.item-img img').attr('src')

            company = {}
            record['company'] = company
            div = item.find('div.stitle')
            a = div.find('a')
            company['name'] = a.attr('title')
            company['href'] = a.attr('href')
            company['years'] = a.prev().text().split(' ')[0]
#             company['location'] = div.find('span.location').text().strip()
            transaction = {'counts': '', 'volume': ''}
            company['transaction'] = transaction
            company['response_rate'] = ''

            div = item.find('div.sstitle')
            a = div.find('a.diamond-level-group')
            diamond = len(a.find('i.ui2-icon-svg-diamond-level-one'))
            half_diamond =len(a.find('i.ui2-icon-svg-diamond-level-half-filled'))
            transaction['level'] = diamond + half_diamond*0.5
#             if 'Transaction' in li.find('div.lab').text():
#                 transaction['counts'] = div.find('ul.record li:first-child div.lab').text().split(' ')[0]
#                 transaction['volume'] = div.find('ul.record li:first-child div.num').text()
            div = item.find('div.num')
            if div:
                company['response_rate'] = div.find('i').text()

#         doc = pq(html)
        
#         for idx, item in enumerate(doc.find('div.m-product-item')):
#             item = pq(item)

#             record = {}
            
#             record['location'] = {}
#             record['location']['page'] = self.current_page
#             record['location']['position'] = idx+1
            
#             if item.find('span.sking'):
#                 record['is_top_sponsor'] = True
#             else:
#                 record['is_top_sponsor'] = False

#             if item.find('span.sl'):
#                 record['is_sponsor'] = True
#             else:
#                 record['is_sponsor'] = False

#             product = {}
#             record['product'] = product
#             product['id'] = item.find('h2.title a').attr('data-hislog')
#             product['title'] = item.find('h2.title').text()
#             product['href'] = item.find('h2.title a').attr('href')
#             product['img'] = item.find('div.item-sub div.img-wrap a img').attr('src')

#             company = {}
#             record['company'] = company
#             div = item.find('div.item-extra')
#             company['name'] = div.find('div.stitle a').text()
#             company['href'] = div.find('div.stitle a').attr('href')
#             company['years'] = div.find('div.stitle div').text().split(' ')[0]
#             company['location'] = div.find('span.location').text().strip()
#             transaction = {'counts': '', 'volume': ''}
#             company['transaction'] = transaction
#             company['response_rate'] = ''

#             diamond = len(div.find('a.s-val i.ui2-icon-svg-diamond-level-one'))
#             half_diamond =len(div.find('a.s-val i.ui2-icon-svg-diamond-level-half-filled'))
#             transaction['level'] = diamond + half_diamond*0.5
#             for li in div.find('ul.record li'):
#                 li = pq(li)
#                 if 'Transaction' in li.find('div.lab').text():
#                     transaction['counts'] = div.find('ul.record li:first-child div.lab').text().split(' ')[0]
#                     transaction['volume'] = div.find('ul.record li:first-child div.num').text()
#                 if 'Response' in li.find('div.lab').text():
#                     company['response_rate'] = div.find('ul.record li:last-child div.num').text()
                    
            records.append(record)
        return records
    
    def next_page(self, keyword):
        self.current_page += 1
        if self.current_page == 1:
            url = self.api + re.sub(' +', '+', keyword)
        else:
            url = self.api + re.sub(' +', '+', keyword) + '&page='+str(self.current_page)
        print(str(self.current_page), end=', ')

        self.get(url)
        return self.browser.page_source
    
    def get(self, url):
        while True:
            try:
                self.browser.get(url)
                time.sleep(1)
                break
            except WebDriverException as e:
                if 'chrome not reachable' in str(e):
                    self.open_browser()
                    if url != 'https://www.alibaba.com':
                        self.get('https://www.alibaba.com')
                    continue
            
        while True:
            readyState = self.browser.execute_script('return document.readyState')
            if readyState == 'interactive' or readyState == 'complete':
                break
            else:
                time.sleep(0.1)
    
    def crawl_product_ranking(self, keyword, pages):
        self.current_page = 0
        records = []
        print(keyword, end=': ')
        
        while self.current_page < pages:
            html = self.next_page(keyword)
            self.crawl_current_page(html, records=records)
        print('length:', len(records), end=', ')
        print('done!')
        
        obj = {'datetime': pendulum.now().to_datetime_string(), 'records': records}
        JSON.serialize(obj, self.market['directory'] + '_config', 'products_ranking', keyword+'.json')
        return obj