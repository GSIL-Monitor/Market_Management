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

import arrow
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


class P4P():
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"}
    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    headers['Accept-Encoding'] = 'gzip, deflate, br'
    headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'
    # headers['Connection'] = 'Keep-Alive'
    headers['Connection'] = 'close'
    headers['Host'] = 'www.alibaba.com'
    headers['Upgrade-Insecure-Requests'] = '1'

    api = 'https://www2.alibaba.com/manage_ad_keyword.htm'
    keywords_list = {}
    
    def __init__(self, market, lid, lpwd, socketio, namespace=None, room=None):
        self.logger = logging.getLogger(market['name'])
        self.logger.setLevel(logging.DEBUG)
        fh = TimedRotatingFileHandler('log/p4p['+market['name']+'].log', when="d", interval=1,  backupCount=7)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.lid = lid
        self.lpwd = lpwd
        self.socketio = socketio
        self.namespace = namespace
        self.room = room

        self.logger.info('initialize .... '+market['name'])
        self.market = market
        self.keywords_history = []
        self.load_keywords('recording')
        self.load_keywords('monitor')

        self.browser = None
        # self.logger.info('open browser and login')
        # alibaba = Alibaba(lid, lpwd, socketio, namespace, room)
        # alibaba.login()
        # self.browser = alibaba.browser

        self.lock = threading.RLock()
        self.recent_prices = {}

        self.balance = None

    def load_keywords(self, tp):
        if not tp:
            return
        else:
            fn = 'p4p_keywords_list_'+tp+'.json'
            root = self.market['directory'] + '_config'
            kws_list = JSON.deserialize(root, [], fn)
            if kws_list is None:
                kws_list = []
            self.keywords_list[tp] = kws_list

    def set_keywords(self, tp, kws_list):
        self.keywords_list[tp] = kws_list
        fn = 'p4p_keywords_list_'+tp+'.json'
        root = self.market['directory'] + '_config'
        JSON.serialize(self.keywords_list[tp], root, [], fn)
    
    def add_keywords(self, tp, kws):
        self.keywords_list[tp].append(kws)
        fn = 'p4p_keywords_list_'+tp+'.json'
        root = self.market['directory'] + '_config'
        JSON.serialize(self.keywords_list[tp], root, [], fn)
    
    def del_keywords(self, tp, kws):
        if kws in self.keywords_list[tp]:
            self.keywords_list[tp].remove(kws)
            fn = 'p4p_keywords_list_'+tp+'.json'
            root = self.market['directory'] + '_config'
            JSON.serialize(self.keywords_list[tp], root, [], fn)
    
    def crawl_keywords(self):
        keywords = []
        with self.lock:
            self.load_url()

            while True:
                html = self.browser.find_element_by_css_selector("div.keyword-manage .bp-table-main-wraper>table tbody").get_attribute('outerHTML')
                tbody = pq(html)
                trs = tbody.find('tr')

                for tr in trs:
                    kws = {}
                    kws['id'] = pq(tr).find('td:first-child input').val()
                    kws['status'] = pq(tr).find('td.bp-cell-status .bp-dropdown-main i').attr('class').split('-').pop()
                    kws['kws'] = pq(tr).find('td.bp-cell-left').text().strip()
                    kws['group'] = pq(tr).find('td[data-role="table-col-tag"]').text().strip()
                    kws['my_price'] = pq(tr).find('td:nth-child(5) a').text().strip()
                    kws['average_price'] = pq(tr).find('td:nth-child(6)').text().strip()
                    string = pq(tr).find('span.qs-star-wrap i').attr('class')
                    kws['match_level'] = re.search('qsstar-(\d+)',string).group(1)
                    string = pq(tr).find('.bp-icon-progress-orange').html()
                    kws['search_count'] = re.search(':(\d+%)',string).group(1)
                    string = pq(tr).find('.bp-icon-progress-blue').html()
                    kws['buy_count'] = re.search(':(\d+%)',string).group(1)
                    keywords.append(kws)

                if not self.next_page():
                    break

        root = self.market['directory'] + '_config'
        fn = 'p4p_keywords_list.json'
        JSON.serialize(keywords, root, [], fn)
        return keywords

    def crawl(self, group="all", tid=None, socketio=None, tasks=None):
        if tid:
            tasks[tid]['is_running'] = True
            msg = {'name': 'P4P.crawl', 'tid': tid, 'group': group, 'is_last_run': tasks[tid]['is_last_run']}
            socketio.emit('event_task_start_running', msg, namespace='/markets', broadcast=True)

        try:
            keywords = []
            self.load_keywords('recording')
            if tid:
                tasks[tid]['progress'] = 1
                socketio.emit('event_task_progress', {'tid': tid, 'progress': 1}, namespace='/markets', broadcast=True)
            with self.lock:
                self.load_url()
                if tid:
                    tasks[tid]['progress'] = 2
                    socketio.emit('event_task_progress', {'tid': tid, 'progress': 2}, namespace='/markets',
                                  broadcast=True)
                all_kws_count = int(self.browser.find_element_by_css_selector('a.all-kwcount span').text)

                kws_count = 0
                while True:
                    table_reloaded = True
                    css_selector = "div.keyword-manage .bp-table-main-wraper>table"
                    table = self.browser.find_element_by_css_selector(css_selector)
                    # print(self.keywords_list['recording'])
                    idx = 0
                    while True:
                        kws_count += 1
                        if tid:
                            tasks[tid]['progress'] = int(kws_count / all_kws_count * 97) + 3
                            socketio.emit('event_task_progress', {'tid': tid, 'progress': tasks[tid]['progress']},
                                          namespace='/markets', broadcast=True)

                        print(table_reloaded, end=" > ")
                        if table_reloaded:
                            trs = table.find_elements_by_css_selector('tbody tr')
                            table_reloaded = False

                        print('index:', idx, len(trs), end=' > ')
                        if idx >= len(trs):
                            print('')
                            break

                        try:
                            tr = trs[idx]
                            id = tr.find_element_by_css_selector('td:first-child input').get_attribute('value').strip()
                            if id not in self.keywords_list['recording']:
                                print('skipped_not_in_recording')
                                idx += 1
                                continue

                            grp = tr.find_element_by_css_selector('td:nth-child(4)').text.strip()
                            if group != 'all':
                                if group != grp:
                                    print('skipped_not_in_group', group, grp)
                                    idx += 1
                                    continue

                            dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            kws = tr.find_element_by_css_selector('td:nth-child(3)').text.strip()

                            print(kws, end=' > ')

                            if not self.open_price_dialog(tr):
                                print('skipped_2')
                                idx += 1
                                continue

                            sponsors = self.find_sponsors(kws)

                            # @redo: retry to fetch prices
                            prices = []
                            count = 0
                            while count < 10:
                                if count == 0:
                                    prices = self.find_prices()
                                elif count <= 5:
                                    prices = self.find_prices(tr)
                                else:
                                    prices = ['0', '0', '0', '0', '0', '0']
                                    print('failed to get prices, using default zero values')
                                    break

                                if prices is None:
                                    break

                                if len(prices) != 0:
                                    break
                                count += 1
                                time.sleep(5)
                            # if id in self.keywords_list['monitor']:
                            #     if self.find_sponsor_list_position(sponsors=sponsors['sponsor_list']) == 0:
                            #         if self.is_on(tr):
                            #             print('turn_off', end=" > ")
                            #             self.turn_off(tr)
                            #             table_reloaded = True
                            if prices:
                                keywords.append([dt, id, kws, grp, prices, sponsors])
                                if (id not in self.recent_prices):
                                    self.recent_prices[id] = []
                                self.recent_prices[id].append(prices)
                                if len(self.recent_prices[id]) > 5:
                                    self.recent_prices[id].pop(0)

                            idx += 1
                            print(' >>>>>> successful end ')
                        except StaleElementReferenceException as e:
                            table_reloaded = True
                            print(' >>>>>> failed ... .... , retry .... ...')
                            continue

                    if not self.next_page():
                        break
            if tid:
                tasks[tid]['progress'] = 100
                socketio.emit('event_task_progress', {'tid': tid, 'progress': 100}, namespace='/markets',
                              broadcast=True)
            if keywords:
                self.save_crawling_result(keywords)

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
        finally:
            if tid:
                tasks[tid]['is_running'] = False
                tasks[tid]['progress'] = 0
                if tasks[tid]['is_last_run']:
                    del tasks[tid]
                    socketio.emit('event_task_last_run_finished', {'tid': tid}, namespace='/markets', broadcast=True)

    def monitor(self, group='all', tid=None, socketio=None, tasks=None):
        tasks[tid]['is_running'] = True
        msg = {'name': 'P4P.monitor', 'tid': tid, 'group': group, 'is_last_run': tasks[tid]['is_last_run']}
        socketio.emit('event_task_start_running', msg, namespace='/markets', broadcast=True)

        try:
            print('Task Monitor start to run with group="'+group+'"')
            self.load_keywords('monitor')
            tasks[tid]['progress'] = 1
            socketio.emit('event_task_progress', {'tid': tid, 'progress': 1}, namespace='/markets', broadcast=True)
            with self.lock:
                self.load_url()
                tasks[tid]['progress'] = 2
                socketio.emit('event_task_progress', {'tid': tid, 'progress': 2}, namespace='/markets', broadcast=True)
                all_kws_count = int(self.browser.find_element_by_css_selector('a.all-kwcount span').text)

                kws_count = 0
                while True:
                    table_reloaded = True
                    css_selector = "div.keyword-manage .bp-table-main-wraper>table"
                    table = self.browser.find_element_by_css_selector(css_selector)
                    print(self.keywords_list['monitor'])
                    idx = 0
                    while True:
                        kws_count += 1
                        tasks[tid]['progress'] = int(kws_count/all_kws_count*97)+3
                        socketio.emit('event_task_progress', {'tid': tid, 'progress': tasks[tid]['progress']}, namespace='/markets', broadcast=True)

                        print(table_reloaded, end=" > ")
                        if table_reloaded:
                            trs =  table.find_elements_by_css_selector('tbody tr')
                            table_reloaded = False
                            
                        print('index:', idx, len(trs), end=' > ')
                        if idx >= len(trs):
                            print('')
                            break

                        try:
                            tr = trs[idx]
                            ActionChains(self.browser).move_to_element(tr).perform()
                            id = tr.find_element_by_css_selector('td:first-child input').get_attribute('value').strip()
                            if id not in self.keywords_list['monitor']:
                                print('skipped_not_in_monitoring')
                                idx += 1
                                continue

                            if group != 'all':
                                grp = tr.find_element_by_css_selector('td:nth-child(4)').text.strip()
                                if group != grp:
                                    print('skipped_not_in_group', group, grp)
                                    idx += 1
                                    continue

                            dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            kws = tr.find_element_by_css_selector('td:nth-child(3)').text.strip()

                            print(kws, end=' > ')

                            current_position = self.find_sponsor_list_position(kws=kws)
                            if current_position <= 4:
                                print('set_price: at pos 5', end=" > ")
                                self.set_price(tr, position=5)
                            if not self.is_on(tr):
                                print('turn_on', end=" > ")
                                self.turn_on(tr)
                                table_reloaded = True
                            
                            idx += 1
                            print(' >>>>>> successful end ')
                        except StaleElementReferenceException as e:
                            table_reloaded = True
                            print(' >>>>>> failed ... .... , retry .... ...')
                            continue
                        
                    if not self.next_page():
                        break
            tasks[tid]['progress'] = 100
            socketio.emit('event_task_progress', {'tid': tid, 'progress': 100}, namespace='/markets', broadcast=True)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
        finally:
            tasks[tid]['is_running'] = False
            tasks[tid]['progress'] = 0
            if tasks[tid]['is_last_run']:
                del tasks[tid]
                socketio.emit('event_task_last_run_finished', {'tid': tid}, namespace='/markets', broadcast=True)

    def save_crawling_result(self, keywords):
        root = self.market['directory'] + '_config'
        date_str = keywords[0][0].split(' ')[0]
        fn = 'p4p_keywords_crawl_result_'+date_str+'.json.gz'
        JSON.serialize(keywords, root, [], fn, append=True)

    def find_sponsors(self, kws):
        url = 'https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&viewtype=L&CatId=&SearchText=' + re.sub(
            ' +', '+', kws)
        self.headers['Referer'] = url

        response = None
        while response is None:
            try:
                response = requests.get(url, headers=self.headers)
                break
            except Exception as e:
                traceback.print_exc()
                time.sleep(3)
                print('====================== retry in 3 seconds =================================')
                response = None
                continue

        top_sponsor = None
        sponsor_list = []

        result = re.search(r'_search_result_data =(.*)page.setPageData\(_search_result_data\)', response.text,
                           re.M | re.DOTALL)
        obj = json.loads(result.group(1))
        items = obj['normalList']
        for idx, item in enumerate(items):
            company = {}
            if (item['isBrandAd']):
                top_sponsor = company
            elif (item['isP4p']):
                sponsor_list.append(company)
            else:
                break

            company['years'] = item['supplierYear']
            company['name'] = item['supplierName']
            company['url'] = item['supplierHref']
            if 'record' in item:
                company['record'] = []
                if 'transaction' in item['record']:
                    company['record'].append(item['record']['transaction']['num'])
                    company['record'].append('Transactions(6 months)')
                    company['record'].append(item['record']['transaction']['conducted'])
                if 'responseRate' in item['record']:
                    company['record'].append('Response Rate')
                    company['record'].append(item['record']['responseRate'])

        return {'top_sponsor': top_sponsor, 'sponsor_list': sponsor_list}

    # def find_sponsors_backup(self, kws):
    #     with self.lock:
    #         url = 'https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&viewtype=L&CatId=&SearchText='+re.sub(' +', '+', kws)
    #
    #         if len(self.browser.window_handles) == 1:
    #             self.browser.execute_script("window.open()")
    #         self.browser.switch_to_window(self.browser.window_handles[1])
    #
    #         top_sponsor = None
    #         sponsor_list = []
    #
    #         try:
    #             self.browser.get(url)
    #             css_selector = "div.m-product-item .item-extra, div.m-product-item .brand-right-container"
    #             WebDriverWait(self.browser, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
    #
    #             html = self.browser.page_source
    #             soup = BeautifulSoup(html, 'html.parser')
    #
    #             divs = soup.find_all('div', class_='m-product-item')
    #             for idx,div in enumerate(divs):
    #                 # print(kws, idx)
    #                 company = {}
    #                 extra = div.find(class_='item-extra')
    #                 if extra:
    #                     a = extra.find('div', class_='stitle').a
    #                     company['years'] = re.search('year-num(\d+)', str(a.i)).group(1)
    #                     a = a.next_sibling.next_sibling
    #                     company['name'] = a.string.strip()
    #                     company['url'] = 'https:' + a['href']
    #                     ul = extra.find('ul', class_='record')
    #                 else:
    #                     container = div.find('div', class_='brand-right-container')
    #                     text = str(container.find('i', class_='year-num'))
    #                     company['years'] = re.search('year-num(\d+)', text).group(1)
    #                     a = container.find('div', class_='supplier').a
    #                     company['name'] = a.string.strip()
    #                     company['url'] = 'https:' + a['href']
    #                     ul = container.find('ul', class_='record-container')
    #
    #                 if ul:
    #                     company['record'] = [re.sub('\n', '', x).strip() for x in ul.findAll(text=True) if x != '\n']
    #
    #                 if div.find('span', class_='sking'):
    #                     top_sponsor = company
    #                 elif div.find('span', class_='sl'):
    #                     sponsor_list.append(company)
    #                 else:
    #                     break
    #
    #         except Exception as e:
    #             print('Error: ', e)
    #             traceback.print_exc()
    #         finally:
    #             # self.browser.execute_script("window.close()")
    #             self.browser.switch_to_window(self.browser.window_handles[0])
    #
    #     return {'top_sponsor': top_sponsor, 'sponsor_list': sponsor_list}

    def load_url(self):
        while True:
            try:
                if self.browser is None:
                    self.logger.info('open browser and login')
                    alibaba = Alibaba(self.lid, self.lpwd, None, None, None)
                    alibaba.login()
                    self.browser = alibaba.browser
                    self.alibaba = alibaba

                self.browser.get(self.api)
                if 'login.alibaba.com' in self.browser.current_url:
                    self.logger.info('Was out, login again!')
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
                    self.logger.info('Browser Window was closed! Try to open a new browser window.')
                    self.browser = None
                continue

    def open_price_dialog(self, tr):
        success = True
        btn = tr.find_element_by_css_selector('td:nth-child(5) a')
        # self.browser.implicitly_wait(1)
        WebDriverWait(self.browser, 15).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.ui-mask')))
        self.click(btn)

        checkbox = tr.find_element_by_css_selector('td:first-child input')
        if checkbox.is_selected():
            checkbox.click()
            success = False
        return success

    def find_sponsor_list_position(self, kws=None, sponsors=None):
        if not kws and not sponsors:
            raise Exception('kws and sponsors can\'t be None at the same time')

        if kws:
            sponsors = self.find_sponsors(kws)
            sponsor_list = sponsors['sponsor_list']
        elif sponsors:
            sponsor_list = sponsors
        
        idx = 0
        count = 0
        for sponsor in sponsor_list:
            count += 1
            if "glittereyelash.en.alibaba.com" in sponsor['url']:
                idx = count
                break
        return idx

    def find_prices(self, tr=None):  # @redo: 相关度不足，无法进入搜索前5名。
        if tr and not self.open_price_dialog(tr):
            return []

        prices = []
        WebDriverWait(self.browser, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))

        while True:
            try:
                price_table_tbody_selector = ".sc-manage-edit-price-dialog table tbody,.sc-manage-edit-price-dialog p.util-clearfix"
                price_table_tbody = WebDriverWait(self.browser, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, price_table_tbody_selector)))

                if price_table_tbody.tag_name == 'p':
                    prices = None
                    break

                for btn in price_table_tbody.find_elements_by_css_selector('a'):
                    price = btn.text.strip()
                    float(price)
                    prices.append(price)

                print(prices, end=">")

                self.check_balance()
                break
            except StaleElementReferenceException:
                self.browser.implicitly_wait(0.5)
                continue
            except ValueError:
                prices = []
                break
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        return prices

    def check_balance(self):
        balance = self.browser.find_element_by_css_selector(
            '.sc-manage-edit-price-dialog span[data-role="span-balance"]').text
        if self.balance is None:
            self.balance = balance
        elif self.balance != balance:
            diff = format(float(self.balance) - float(balance), '.2f')
            self.balance = balance

            time_str = arrow.now().format('YYYY-MM-DD HH:mm:ss')
            date_str = time_str.split(' ')[0]
            root = self.market['directory'] + '_config'
            fn = 'p4p_balance_change_history_'+date_str+'.json.gz'
            JSON.serialize([time_str, diff], root, [], fn, append=True)

    def next_page(self):
        success = True
        while True:
            try:
                btn_next = self.browser.find_element_by_css_selector('.bp-table-footer a.next')
                ActionChains(self.browser).move_to_element(btn_next).perform()
                css_selector = "div.keyword-manage .bp-table-main-wraper>table tbody tr:first-child"
                tr = self.browser.find_element_by_css_selector(css_selector)
                self.click(btn_next)
                WebDriverWait(self.browser, 15).until(EC.staleness_of(tr))
                self.browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
                break
            except NoSuchElementException as e:
                success = False
                break
            except ElementNotVisibleException as e:
                success = False
                break
            except StaleElementReferenceException as e:
                self.browser.implicitly_wait(1)
                continue
        print('next_page:', success)
        return success

    def set_price(self, tr, position=None, price=None):
        if not position and not price:
            return

        # pos = 3
        max_price = 30
        # sum = 0
        # id = tr.find_element_by_css_selector('td:first-child input').get_attribute('value').strip()
        # for prices in self.recent_prices[id]:
        #     sum += float(prices[pos])
        # mean_price = sum/len(self.recent_prices[id])
        # if max_price > (mean_price + 0.1):
        #     max_price = (mean_price + 0.1)

        if not self.open_price_dialog(tr):
            return False
        
        success = True
        WebDriverWait(self.browser, 15).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))
        while True:
            try:
                price_table_tbody_selector = ".sc-manage-edit-price-dialog table tbody,.sc-manage-edit-price-dialog p.util-clearfix"
                price_table_tbody = WebDriverWait(self.browser, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, price_table_tbody_selector)))

                if price_table_tbody.tag_name == 'p':
                    success = False
                    break

                if price:
                    css_selector = '.sc-manage-edit-price-dialog span[data-role="span-baseprice"'
                    min_price = float(self.browser.find_element_by_css_selector(css_selector).text)
                    if price < min_price:
                        price = min_price
                        
                    js_templ = "document.querySelector('{selector}').value = '{value}';"
                    css_selector = '.sc-manage-edit-price-dialog input[name="addPrice"]'
                    js = js_templ.format(selector=css_selector, value=price)
                    self.browser.execute_script(js)
                else:
                    while True:
                        btn = price_table_tbody.find_element_by_css_selector('td:nth-child('+str(int(position)+1)+') a, td:last-child a')
                        p = float(btn.text.strip())
                        if p <= max_price:
                            self.click(btn)
                            break
                        if position >= 5:
                            break
                        position += 1
                
                confirm = self.browser.find_element_by_css_selector('.ui2-dialog-btn input[data-role="confirm"]')
                self.click(confirm)
                break
            except StaleElementReferenceException:
                self.browser.implicitly_wait(0.5)
                continue
        return success

    def is_on(self, tr):
        i = tr.find_element_by_css_selector('td.bp-cell-status .bp-dropdown-main i')
        if i.get_attribute('class').split('-').pop() == 'start':
            return True
        else:
            return False

    def turn_on(self, tr):
        td = tr.find_element_by_css_selector('td:nth-child(2)')
        self.click(td)
        css_selector = '.bp-table>div.bp-dropdown-hover li.bp-status-start'
        btn_start = WebDriverWait(self.browser, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        self.click(btn_start)
        self.browser.implicitly_wait(1)
        WebDriverWait(self.browser, 15).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))
        
    def turn_off(self, tr):
        td = tr.find_element_by_css_selector('td:nth-child(2)')
        self.click(td)
        css_selector = '.bp-table>div.bp-dropdown-hover li.bp-status-stop'
        btn_stop = WebDriverWait(self.browser, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        self.click(btn_stop)
        self.browser.implicitly_wait(1)
        WebDriverWait(self.browser, 15).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))

    def click(self, btn):
        while True:
            try:
                btn.click()
                break
            except WebDriverException as e:
                if 'is not clickable at point' in str(e):
                    self.browser.implicitly_wait(0.5)
                    continue
                else:
                    raise e

    def turn_all_off(self, group='all', monitored=True, tid=None, socketio=None, tasks=None):
        tasks[tid]['is_running'] = True
        msg = {'name': 'P4P.turn_all_off', 'tid': tid, 'group': group, 'monitored': monitored, 'is_last_run': tasks[tid]['is_last_run']}
        socketio.emit('event_task_start_running', msg, namespace='/markets', broadcast=True)
        try:
            tasks[tid]['progress'] = 1
            socketio.emit('event_task_progress', {'tid': tid, 'progress': 1}, namespace='/markets', broadcast=True)
            with self.lock:
                self.load_url()
                tasks[tid]['progress'] = 2
                socketio.emit('event_task_progress', {'tid': tid, 'progress': 2}, namespace='/markets', broadcast=True)
                all_kws_count = int(self.browser.find_element_by_css_selector('a.all-kwcount span').text)

                kws_count = 0
                while True:
                    css_selector = "div.keyword-manage .bp-table-main-wraper>table"
                    table = self.browser.find_element_by_css_selector(css_selector)

                    trs = table.find_elements_by_css_selector('tbody tr')

                    selected = False
                    for tr in trs:
                        kws_count += 1
                        tasks[tid]['progress'] = int(kws_count/all_kws_count*97)+3
                        socketio.emit('event_task_progress', {'tid': tid, 'progress': tasks[tid]['progress']}, namespace='/markets', broadcast=True)
                        id = tr.find_element_by_css_selector('td:first-child input').get_attribute('value').strip()
                        if monitored and id not in self.keywords_list['monitor']:
                            continue

                        if group != 'all':
                            if group != tr.find_element_by_css_selector('td:nth-child(4)').text.strip():
                                continue

                        if self.is_on(tr):
                            tr.find_element_by_css_selector("td:first-child input").click()
                            selected = True

                    if selected:
                        css_selector = '.bp-table .toolbar a[data-role="btn-pause"]'
                        btn_pause = self.browser.find_element_by_css_selector(css_selector)
                        self.click(btn_pause)

                        self.browser.implicitly_wait(1)
                        WebDriverWait(self.browser, 15).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))
                    
                    time.sleep(10)
                    if not self.next_page():
                        break
            tasks[tid]['progress'] = 100
            socketio.emit('event_task_progress', {'tid': tid, 'progress': 100}, namespace='/markets', broadcast=True)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
        finally:
            tasks[tid]['is_running'] = False
            tasks[tid]['progress'] = 0
            if tasks[tid]['is_last_run']:
                del tasks[tid]
                socketio.emit('event_task_last_run_finished', {'tid': tid}, namespace='/markets', broadcast=True)
