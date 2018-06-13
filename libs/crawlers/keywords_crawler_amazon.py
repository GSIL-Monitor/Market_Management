import time
from .keywords_crawler import KewordsCrawler

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class KwclrAmazon(KewordsCrawler):
    # browser = None
    # keyword = None
    # socket = None
    # page_quantity = 1
    # current_pn = 0

    api = 'https://www.amazon.com/s?field-keywords='

    # we_next_page = None
    cl_item = '#atfResults ul li'
    cl_title = '.a-col-right .a-spacing-small a'
    # cl_keywords = 'div.tags'
    cl_img = '.a-col-left img'
    # cl_crown = 'div.item-info h2>i.ui2-icon-crown'
    cl_ad = '.a-col-right>h5'

    def crawl(self):
        results = []
        items = self.browser.find_elements_by_css_selector(self.cl_item)
        
        for item in items:
            result = {'title': "", 'keywords': [], 'img': ""}
            try:
                result['title'] = item.find_element_by_css_selector(self.cl_title).get_attribute('title')
                result['href'] = item.find_element_by_css_selector(self.cl_title).get_attribute('href')
                result['img'] = item.find_element_by_css_selector(self.cl_img).get_attribute('src')
                # if not result['img']:
                #     result['img'] = item.find_element_by_css_selector(self.cl_img).get_attribute('data-jssrc')
            except NoSuchElementException:
                continue

            try:
                item.find_element_by_css_selector(self.cl_ad)
                result['isAd'] = True
            except NoSuchElementException:
                result['isAd'] = False

            results.append(result)
        return results

    def next_page(self):
        self.current_pn = self.current_pn + 1
        if self.current_pn == 1:
            url = self.api + '+'.join(self.keyword.split(' '))
        else:
            url = self.api + '-'.join(self.keyword.split(' ')) + '&page=' + str(self.current_pn)

        msg = {'type':'primary'}
        msg['content'] = '正在抓取产品列表，第'+str(self.current_pn)+'页，网址：'+url
        self.socket.emit('notify', msg, namespace='/markets', room=self.sid)

        self.browser.get(url)