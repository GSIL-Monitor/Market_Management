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

    def __init__(self, market, account=None, headless=True, browser=None):
        self.market = market
        self.account = account
        self.lid = account['lid'] if account else market['lid']
        self.lpwd = account['lpwd'] if account else market['lpwd']
        self.lname = account['lname'] if account else market['lname']
        self.mobile = account['mobile'] if account else market['mobile']

        self.account = {}
        self.account['lid'] = self.lid
        self.account['lpwd'] = self.lpwd
        self.account['lname'] = self.lname
        self.account['mobile'] = self.mobile

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
        rp['flat eyelash'] = {'ali_id': '60764332933', 'price': 3.9}
        rp['premade fans glue bonded'] = {'ali_id': '60762376749', 'price': 0.9}
        rp['premade fans heat bonded'] = {'ali_id': '60795873604', 'price': 1.9}

        self.recommended = {}
        self.recommended['mink eyelash'] = [rp['mink eyelash'], rp['silk eyelash'], rp['magnetic eyelash']]
        self.recommended['silk eyelash'] = [rp['silk eyelash'], rp['mink eyelash'], rp['magnetic eyelash']]
        self.recommended['magnetic eyelash'] = [rp['magnetic eyelash'], rp['mink eyelash'], rp['silk eyelash']]
        self.recommended['flat eyelash'] = [rp['flat eyelash'], rp['individual eyelash'], rp['premade fans glue bonded'], rp['premade fans heat bonded']]
        self.recommended['individual eyelash'] = [rp['individual eyelash'], rp['flat eyelash'], rp['premade fans glue bonded'], rp['premade fans heat bonded']]
        self.recommended['glue bonded'] = [rp['premade fans glue bonded'], rp['premade fans heat bonded'], rp['individual eyelash'], rp['flat eyelash']]
        self.recommended['heat bonded'] = [rp['premade fans heat bonded'], rp['premade fans glue bonded'], rp['individual eyelash'], rp['flat eyelash']]
        self.recommended['premade fans'] = self.recommended['glue bonded']
        self.recommended['default'] = self.recommended['mink eyelash'] + self.recommended['individual eyelash']

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
            
        dt_1400 = pendulum.parse('14:00', tz='Asia/Shanghai')
        dt_1500 = pendulum.parse('15:00', tz='Asia/Shanghai')
        if dt_1400 < pendulum.now() < dt_1500:
            self.switch_to_last_31_days()

        self.browser.implicitly_wait(0.5)
        WebDriverWait(self.browser, 15).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div#J-visitors-tip-loading')))

        div_overview_has_mails = WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.overview-has-mails')))
        remain = div_overview_has_mails.find_element_by_css_selector('span.overview-remain').get_attribute('data-remain')
        remain = int(remain)

        if remain == 0:
            print('20 个 可营销 名额 已用尽！')
            return

        check_box = self.browser.find_elements_by_css_selector('input#J-condition-mailable')
        if check_box:
            check_box[0].click()

        while remain>0:
            remain = self.mail_to_current_page_visitors(remain)
            if not self.next_page():
                break

    def mail_to_current_page_visitors(self, remain):
        css_tbody = '#J-visitors-tbl-tbody'
        tbody = WebDriverWait(self.browser, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, css_tbody)))

        count = 0
        for tr in tbody.find_elements_by_css_selector(css_tbody+' tr.J-visitors-table-tr'):
            if count >= remain:
                break
            ActionChains(self.browser).move_to_element(tr).perform()
            
            visitor = self.parse_tr(tr)
            
            rps = []
            for pv in visitor['pv-detail']:
                url = pv['page']
                result = re.search('(_|\/)(\d+)(\.html|\/)', url, re.IGNORECASE)
                if result:
                    ali_id = result.group(2)
                    category = self.products[ali_id]['category'].lower()
                    for key in self.recommended:
                        if key in category:
                            for rp in self.recommended[key]:
                                if rp not in rps:
                                    rps.append(rp)
                            break
            
            self.mail_to_visitor(tr, rps)
            count += 1

        return remain - count

    def mail_to_visitor(self, tr, recommendation):
        td = tr.find_element_by_css_selector('td:last-child')
        spans = td.find_elements_by_css_selector('span.mailable')
        if not spans:
            return False
        
        span = td.find_element_by_css_selector('span.mail-send')
        span.click()
        WebDriverWait(self.browser, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.ui-mask')))
        
        confirm_button = None
        while True:
            confirm_window = self.browser.find_elements_by_css_selector('div.ui-window')
            if not confirm_window or not confirm_window[-1].is_displayed():
                self.browser.implicitly_wait(0.5)
                continue

            confirm_button = confirm_window[-1].find_element_by_css_selector('input[data-role="confirm"]')
            break
            
        # 点击 “营销”
        confirm_button.click()
        if len(self.browser.window_handles) == 1:
            return False
        
        self.browser.switch_to_window(self.browser.window_handles[1])
        
        # 切换至新 Tab
        form = self.browser.find_element_by_css_selector('div.negotiation-product-form')
        div_product_items = form.find_element_by_css_selector('div.product-editable div[data-role="product-items"]')
        
        # remove first product item
        product_item = div_product_items.find_element_by_css_selector('div.product-item:first-child')
        product_item.find_element_by_css_selector('div.remove-item a').click()
        
        for rp in recommendation:
            ali_id = rp['ali_id']
            print('-----------------', ali_id, '---------------------')
            
            subject = self.products[ali_id]['title']
        
            btn_choose_product = form.find_element_by_css_selector('a[data-role="chooseProduct"]')
            btn_choose_product.click()
            WebDriverWait(self.browser, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.ui-modal')))
            
            # switch to iframe
            WebDriverWait(self.browser, 3).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe.simple-content-iframe')))
            
            WebDriverWait(self.browser, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'ul#sp-products-list li:first-child')))
            
            btn_search = self.browser.find_element_by_css_selector('input#sp-basicSearchSubmit')
            self.browser.execute_script("document.getElementById('sp-basicSearchSubject').value='"+subject+"'")
            
            ul_last_product = self.browser.find_elements_by_css_selector('ul#sp-products-list li:last-child')
            btn_search.click()
            if ul_last_product:
                WebDriverWait(self.browser, 3).until(EC.staleness_of(ul_last_product[0]))
                
            last_li = None
            found = False
            while True:
                
                if last_li:
                    WebDriverWait(self.browser, 3).until(EC.staleness_of(last_li))
                WebDriverWait(self.browser, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'ul#sp-products-list li:first-child')))
                    
                lis_products = self.browser.find_elements_by_css_selector('ul#sp-products-list li')
                print(len(lis_products))
                for li in lis_products:
                    last_li = li
                    if ali_id in li.get_attribute('id'):
                        li.click()
                        found = True
                        break

                if found:
                    break

                btn_next = self.browser.find_element_by_css_selector('div#sp-paginator a:last-child')
                if not btn_next.is_displayed():
                    break
                else:
                    btn_next.click()
                    
            btn_add_product_submit = self.browser.find_element_by_css_selector('input#sp-addProductSubmit')
            btn_add_product_submit.click()
            
            # switch back from iframe
            self.browser.switch_to.default_content()
            
            div = None
            while True:
                div = self.browser.find_elements_by_css_selector('div.product-item[data-pid="'+ali_id+'"]')
                if div:
                    div = div[0]
                    break
                else:
                    self.browser.implicitly_wait(0.5)
            
            # fill the quantity
    #         div = self.browser.find_element_by_css_selector('div.product-item[data-pid="'+ali_id+'"]')
            input_quantity = div.find_element_by_css_selector('input[name="quantity"]')
            input_quantity.send_keys('1')
            # select unit
            unit = self.products[ali_id]['price'].split('/')[-1].strip()
            div.find_element_by_css_selector('div.products-unit').click()
            ul_unit_list = div.find_element_by_css_selector('div[data-role="unit-list"] ul')
            WebDriverWait(self.browser, 3).until(EC.visibility_of(ul_unit_list))
            for li in ul_unit_list.find_elements_by_css_selector('li'):
                if li.text.startswith(unit):
                    ActionChains(self.browser).move_to_element(li).perform()
                    li.click()
                    break
            # set the price
            input_price = div.find_element_by_css_selector('input[name="unitPrice"]')
            input_price.send_keys(str(rp['price']))
            
            div.find_element_by_css_selector('div.products-price').click()
            
        self.browser.execute_script('document.querySelector("textarea").value="'+self.mail_message+'"')
        
        btn_send = visitor.browser.find_element_by_css_selector('a.aui-leads-send-button')
        ActionChains(self.browser).move_to_element(btn_send).perform()
        btn_send.click()
        WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.ui2-feedback-success')))
        
        self.browser.close()
        self.browser.switch_to_window(self.browser.window_handles[0])