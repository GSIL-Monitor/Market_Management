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

import pendulum
import arrow
from datetime import datetime
from pyquery import PyQuery as pq

import redis
import json
import requests
import time
import re

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
    
    def __init__(self, market, lid, lpwd, broker_url=None, headless=True, browser=None):
        self.logger = logging.getLogger(market['name'])
        self.logger.setLevel(logging.DEBUG)
        fh = TimedRotatingFileHandler('log/p4p['+market['name']+'].log', when="d", interval=1,  backupCount=7)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.lid = lid
        self.lpwd = lpwd
        self.broker_url = broker_url

        if self.broker_url:
            self.redis = redis.StrictRedis.from_url(self.broker_url)

        self.logger.info('initialize .... '+market['name'])
        self.market = market
        self.keywords_history = []
        self.load_keywords('recording')
        self.load_keywords('monitor')

        self.alibaba = None
        self.headless = headless
        self.browser = browser
        # self.logger.info('open browser and login')
        # alibaba = Alibaba(lid, lpwd, socketio, namespace, room)
        # alibaba.login()
        # self.browser = alibaba.browser

        self.lock = threading.RLock()
        self.recent_prices = {}

        self.balance = None
        self.initial_balance = 300
        self.default_position = 5
        self.kws_tracking = {}

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
                    groups = pq(tr).find('td[data-role="table-col-tag"]').text().strip()
                    kws['my_price'] = pq(tr).find('td:nth-child(5) a').text().strip()
                    kws['average_price'] = pq(tr).find('td:nth-child(6)').text().strip()
                    string = pq(tr).find('span.qs-star-wrap i').attr('class')
                    kws['match_level'] = re.search('qsstar-(\d+)',string).group(1)
                    string = pq(tr).find('.bp-icon-progress-orange').html()
                    kws['search_count'] = re.search(':(\d+%)',string).group(1)
                    string = pq(tr).find('.bp-icon-progress-blue').html()
                    kws['buy_count'] = re.search(':(\d+%)',string).group(1)
                    for grp in groups.split(','):
                        group = grp.strip()
                        obj = kws.copy()
                        obj['group'] = group
                        keywords.append(obj)

                if not self.next_page():
                    break

        root = self.market['directory'] + '_config'
        fn = 'p4p_keywords_list.json'
        JSON.serialize(keywords, root, [], fn)
        return keywords

    def crawl(self, group="all"):

        try:
            keywords = []
            # self.load_keywords('recording')

            with self.lock:
                self.load_url()

                # all_kws_count = int(self.browser.find_element_by_css_selector('a.all-kwcount span').text)
                all_kws_count = self.switch_to_group(group)

                kws_count = 0
                while True:
                    css_selector = "div.keyword-manage .bp-table-main-wraper>table"
                    table = self.browser.find_element_by_css_selector(css_selector)

                    trs = table.find_elements_by_css_selector('tbody tr')

                    has_checked = False
                    for idx, tr in enumerate(trs):
                        kws_count += 1

                        print('index:', idx, len(trs), end=' > ')
                        ActionChains(self.browser).move_to_element(tr).perform()
                        id = tr.find_element_by_css_selector('td:first-child input').get_attribute('value').strip()
                        # if id not in self.keywords_list['recording']:
                        #     print('skipped_not_in_recording')
                        #     continue

                        grp = tr.find_element_by_css_selector('td:nth-child(4)').text.strip()
                        if group != 'all':
                            if group not in grp:
                                print('skipped_not_in_group', group, grp)
                                continue

                        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        kws = tr.find_element_by_css_selector('td:nth-child(3)').text.strip()

                        print(kws, end=' > ')

                        if not self.open_price_dialog(tr):
                            print('skipped_2')
                            continue

                        [prices, sponsors] = self.find_prices_and_sponsors()

                        if prices:
                            keywords.append([dt, id, kws, grp, prices, sponsors])

                            if (id not in self.recent_prices):
                                self.recent_prices[id] = []
                            self.recent_prices[id].append(prices)
                            if len(self.recent_prices[id]) > 5:
                                self.recent_prices[id].pop(0)

                        print(' >>>>>> successful end ')

                    if not self.next_page():
                        break

            if keywords:
                self.save_crawling_result(keywords)

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
        finally:
            pass

    def monitor(self, group='all', sub_budget_limited=False):
        if sub_budget_limited and self.redis.get(self.market['name'] + '_p4p_sub_budget') is not None:
            if float(self.redis.get(self.market['name'] + '_p4p_sub_budget')) < 0:
                if self.redis.get(self.market['name'] + '_p4p_sub_budget_overflow') is not None:
                    self.turn_all_off(group=group)
                    self.redis.delete(self.market['name'] + '_p4p_sub_budget_overflow')
                return

        try:
            print('Task Monitor start to run with group="' + group + '"')
            keywords = []
            # self.load_keywords('monitor')

            with self.lock:
                self.load_url()

                # all_kws_count = int(self.browser.find_element_by_css_selector('a.all-kwcount span').text)
                print('switch to group:', group)
                all_kws_count = self.switch_to_group(group)
                #             time.sleep(5)
                # self.browser.execute_script("document.body.style.zoom='90%'")
                
                kws_count = 0
                while True:
                    css_selector = "div.keyword-manage .bp-table-main-wraper>table"
                    table = self.browser.find_element_by_css_selector(css_selector)

                    trs = table.find_elements_by_css_selector('tbody tr')

                    has_checked = False
                    for idx, tr in enumerate(trs):
                        kws_count += 1

                        print('index:', idx, len(trs), end=' > ')
                        ActionChains(self.browser).move_to_element(tr).perform()
                        id = tr.find_element_by_css_selector('td:first-child input').get_attribute('value').strip()
                        # if id not in self.keywords_list['monitor']:
                        #     print('skipped_not_in_monitoring')
                        #     continue

                        grp = tr.find_element_by_css_selector('td:nth-child(4)').text.strip()
                        if group != 'all':
                            if group not in grp:
                                print('skipped_not_in_group', group, grp)
                                continue

                        dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        kws = tr.find_element_by_css_selector('td:nth-child(3)').text.strip()

                        print(kws, end=' > ')

                        if not self.open_price_dialog(tr):
                            print('skipped_2')
                            continue

                        [prices, sponsors] = self.find_prices_and_sponsors(close=False)

                        if prices:
                            keywords.append([dt, id, kws, grp, prices, sponsors])

                        current_position = self.find_sponsor_list_position(sponsors=sponsors['sponsor_list'])
                        
                        click_position = self.get_click_position(id, current_position)

                        if click_position != -1:
                            self.set_price(position=click_position)
                        else:
                            webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()

                        WebDriverWait(self.browser, 15).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.ui-mask')))

                        if not self.is_on(tr):
                            print('make selected', end=" > ")
                            tr.find_element_by_css_selector("td:first-child input").click()
                            has_checked = True

                        print(' >>>>>> successful end ')

                    if has_checked:
                        css_selector = '.bp-table .toolbar a[data-role="btn-start"]'
                        btn_start = self.browser.find_element_by_css_selector(css_selector)
                        self.click(btn_start)
                        print('switch selected on.')

                        self.browser.implicitly_wait(1)
                        WebDriverWait(self.browser, 15).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))

                    if not self.next_page():
                        break

            if keywords:
                self.save_crawling_result(keywords)

            if sub_budget_limited and self.redis.get(self.market['name'] + '_p4p_sub_budget') is not None:
                if float(self.redis.get(self.market['name'] + '_p4p_sub_budget')) < 0:
                    if self.redis.get(self.market['name']+'_p4p_sub_budget_overflow') is not None:
                        self.turn_all_off(group=group)
                        self.redis.delete(self.market['name'] + '_p4p_sub_budget_overflow')

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
        finally:
            pass

    def save_crawling_result(self, keywords):
        root = self.market['directory'] + '_config'
        date_str = keywords[0][0].split(' ')[0]
        fn = 'p4p_keywords_crawl_result_'+date_str+'.json.gz'
        JSON.serialize(keywords, root, [], fn, append=True)

    def load_url(self):
        while True:
            try:
                if self.alibaba is None:
                    self.logger.info('open browser and login')
                    alibaba = Alibaba(self.lid, self.lpwd, headless=self.headless, browser=self.browser)
                    alibaba.login()
                    if self.browser is None:
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

    def switch_to_group(self, group='all'):
        if group == "all":
            return int(self.browser.find_element_by_css_selector('a.all-kwcount span').text)
        group_list = self.browser.find_elements_by_css_selector('div.keyword-group ul.group-list li')
        group_li = None

        for li in group_list:
            grp = li.get_attribute('data-name')
            if grp == group:
                group_li = li
                break

        count = 0
        if group_li:
            count = int(re.search('\((\d+)\)', group_li.text).group(1))
            group_li.click()
            WebDriverWait(self.browser, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))
        return count

    def open_price_dialog(self, tr):
        success = True
        btn = tr.find_element_by_css_selector('td:nth-child(5) a')
        self.click(btn)

        WebDriverWait(self.browser, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.ui-mask')))

        WebDriverWait(self.browser, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))

        checkbox = tr.find_element_by_css_selector('td:first-child input')
        if checkbox.is_selected():
            checkbox.click()
            success = False
        return success

    def find_sponsors(self, kws):

        top_sponsor = None
        sponsor_list = []

        url = 'https://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&viewtype=L&CatId=&SearchText=' + re.sub(
            ' +', '+', kws)
        self.headers['Referer'] = url

        response = None
        result = None
        while response is None:
            try:
                response = requests.get(url, headers=self.headers, timeout=(3, 10))

                result = re.search(r'_search_result_data =(.*)page.setPageData\(_search_result_data\)', response.text,
                               re.M | re.DOTALL)

                result = re.sub(',[\n\t ]*}', '}',result.group(1))
                result = re.sub('"" === "true"', '"\\"\\" === \\"true\\""', result)

                break

            except Exception as e:
                print('Error: ', e)
                traceback.print_exc()
                time.sleep(3)
                print('============================== retry in 3 seconds =================================')
                response = None
                continue

        obj = json.loads(result)
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

    def find_prices_and_sponsors(self, close=True):
        prices = []

        kws = self.browser.find_element_by_css_selector(
            '.sc-manage-edit-price-dialog span[data-role="span-keyword"]').text.strip()
        sponsors = self.find_sponsors(kws)

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

                self.check_balance()
                break
            except StaleElementReferenceException as e:
                #             self.browser.implicitly_wait(0.5)
                print('Error: ', e)
                traceback.print_exc()
                time.sleep(0.5)
                continue
            except ValueError:
                # prices = []
                break
        if close:
            webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()

        return [prices, sponsors]

    def find_sponsor_list_position(self, kws=None, sponsors=None):
        if not kws and not sponsors:
            raise Exception('kws and sponsors can\'t be None at the same time')

        if kws:
            sponsors = self.find_sponsors(kws)
            sponsor_list = sponsors['sponsor_list']
        elif sponsors:
            sponsor_list = sponsors
        
        idx = -1
        count = 0
        homepage = re.search('([^\/]+\.en\.alibaba\.com)', self.market['homepage']).group(1)
        for sponsor in sponsor_list:
            count += 1
            if homepage in sponsor['url']:
                idx = count
                break
        return idx

    def get_click_position(self, kws_id, current_pos):
        now = pendulum.now()
        if kws_id not in self.kws_tracking:
            tracking = {}
            tracking['position'] = [self.default_position, now, False]
            self.kws_tracking[kws_id] = tracking
            return self.default_position
        else:
            tracking = self.kws_tracking[kws_id]
            [pos, dt, is_out] = tracking['position']
            if current_pos == -1:
                pos = 3
                tracking['position'] = [pos, now, True]
                return pos
            elif is_out:
                period = now.diff(dt).in_minutes()
                if period <= 5:
                    if current_pos >= 3:
                        return -1
                    else:
                        pos = 3
                        tracking['position'] = [pos, dt, True]
                elif 5 < period <= 15:
                    if current_pos >= 4:
                        return -1
                    else:
                        pos = 4
                        tracking['position'] = [pos, dt, True]
                else:
                    pos = 5
                    tracking['position'] = [pos, dt, False]
                return pos
            elif current_pos == self.default_position:
                return -1
            else:
                return self.default_position
                # calculate the escaped time since in this position

    def check_balance(self):
        balance = self.browser.find_element_by_css_selector(
            '.sc-manage-edit-price-dialog span[data-role="span-balance"]').text

        if self.broker_url:
            self.balance = self.redis.getset(self.market['name']+'_p4p_balance', balance)

            if float(balance) == self.initial_balance or self.balance is None:
                return
            else:
                self.balance = self.balance.decode()
                if self.balance != balance:
                    diff = format(float(self.balance) - float(balance), '.2f')

                    changes = 0 - float(diff)
                    sub_budget = self.redis.get(self.market['name'] + '_p4p_sub_budget')
                    if sub_budget is not None and float(sub_budget) > 0:
                        if self.redis.incrbyfloat(self.market['name'] + '_p4p_sub_budget', changes) < 0:
                            self.redis.set(self.market['name'] + '_p4p_sub_budget_overflow', True)

                    time_str = arrow.now().format('YYYY-MM-DD HH:mm:ss')
                    date_str = time_str.split(' ')[0]
                    root = self.market['directory'] + '_config'
                    fn = 'p4p_balance_change_history_' + date_str + '.json.gz'
                    JSON.serialize([time_str, diff], root, [], fn, append=True)
        else:
            if self.balance is None:
                self.balance = balance
            elif float(balance) == self.initial_balance:
                return
            elif self.balance != balance:
                diff = format(float(self.balance) - float(balance), '.2f')
                self.balance = balance

                time_str = arrow.now().format('YYYY-MM-DD HH:mm:ss')
                date_str = time_str.split(' ')[0]
                root = self.market['directory'] + '_config'
                fn = 'p4p_balance_change_history_'+date_str+'.json.gz'
                JSON.serialize([time_str, diff], root, [], fn, append=True)

    def set_sub_budget(self, sub_budget):
        self.redis.set(self.market['name'] + '_p4p_sub_budget', sub_budget)

    def unset_sub_budget(self):
        self.redis.delete(self.market['name'] + '_p4p_sub_budget')

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

    def set_price(self, tr=None, position=None, price=None):
        if not position and not price:
            return

        # pos = 3
        max_price = 31
        # sum = 0
        # id = tr.find_element_by_css_selector('td:first-child input').get_attribute('value').strip()
        # for prices in self.recent_prices[id]:
        #     sum += float(prices[pos])
        # mean_price = sum/len(self.recent_prices[id])
        # if max_price > (mean_price + 0.1):
        #     max_price = (mean_price + 0.1)

        if tr and not self.open_price_dialog(tr):
            return False

        success = True
        WebDriverWait(self.browser, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))
        while True:
            try:
                price_table_tbody_selector = ".sc-manage-edit-price-dialog table tbody,.sc-manage-edit-price-dialog p.util-clearfix"
                price_table_tbody = WebDriverWait(self.browser, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, price_table_tbody_selector)))

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
                        btn = price_table_tbody.find_element_by_css_selector(
                            'td:nth-child(' + str(int(position) + 1) + ') a, td:last-child a')
                        p = btn.text.strip()
                        if p == '--':
                            pre_position = int(position) - 1
                            position = str(pre_position)
                            continue

                        cp = self.browser.find_element_by_css_selector(
                            '.sc-manage-edit-price-dialog input[name="addPrice"]').get_attribute('value')

                        if cp == p:
                            webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
                            print('不需要改变价格', end=' > ')
                            return success
                        if float(p) <= max_price:
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

    def turn_all_off(self, group='all'):
        try:
            with self.lock:
                self.load_url()
                all_kws_count = self.switch_to_group(group)
                kws_count = 0
                while True:
                    css_selector = "div.keyword-manage .bp-table-main-wraper>table"
                    table = self.browser.find_element_by_css_selector(css_selector)

                    trs = table.find_elements_by_css_selector('tbody tr')

                    selected = False
                    for tr in trs:
                        kws_count += 1
                        id = tr.find_element_by_css_selector('td:first-child input').get_attribute('value').strip()
                        # if monitored and id not in self.keywords_list['monitor']:
                        #     continue

                        if group != 'all':
                            grp = tr.find_element_by_css_selector('td:nth-child(4)').text.strip()
                            if group not in grp:
                                continue

                        if self.is_on(tr):
                            tr.find_element_by_css_selector("td:first-child input").click()
                            selected = True

                    if selected:
                        css_selector = '.bp-table .toolbar a[data-role="btn-pause"]'
                        btn_pause = self.browser.find_element_by_css_selector(css_selector)
                        self.click(btn_pause)

                        self.browser.implicitly_wait(1)
                        WebDriverWait(self.browser, 15).until(
                            EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.bp-loading-panel')))

                    if not self.next_page():
                        break

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()
        finally:
            self.kws_tracking = {}
