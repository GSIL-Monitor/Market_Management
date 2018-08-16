import re
import time
from .keywords_crawler import KewordsCrawler
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

class KwclrAliSp(KewordsCrawler):
    # browser = None
    # keyword = None
    # socket = None
    # page_quantity = 1
    # current_pn = 0

    api = None

    # we_next_page = None
    cl_max_pn = '#site_content div.ui-pagination-pager label'
    cl_item = '#products-container div.list-item'
    cl_title = '.product-title a'
    xp_keywords = '//meta[@name="keywords"]'
    cl_img = '.product-img img'
    cl_crown = 'div.item-info h2>i.ui2-icon-crown'
    cl_ad = 'div.item-info h2>div.seo-ad-flag>.sl'

    products = {}
    product_urls = []

    def crawl(self):
        results = []
        
        try:
            label = self.browser.find_element_by_css_selector(self.cl_max_pn)
        except NoSuchElementException:
            pass

        self.max_pn = int(label.text.strip().split(' ')[2])
        
        items = self.browser.find_elements_by_css_selector(self.cl_item)
        for item in items:
            result = {'title': "", 'keywords': [], 'img': ""}
            result['title'] = item.find_element_by_css_selector(self.cl_title).get_attribute('title')
            href = item.find_element_by_css_selector(self.cl_title).get_attribute('href')
            result['href'] = href
            result['img'] = item.find_element_by_css_selector(self.cl_img).get_attribute('src')

            result['isCrowned'] = False
            result['isAd'] = False

            self.product_urls.append(href)
            self.products[href] = result
            results.append(result)

        count = 1
        for url in self.product_urls:
            msg = {'type':'primary'}
            msg['content'] = '正在抓取产品列表，第'+str(self.current_pn)+'页，第'+str(count)+'个产品详情页，网址：'+url
            self.socket.emit('notify', msg, namespace='/markets', room=self.sid)

            self.browser.get(url)
            # time.sleep(1)
            self.crawl_product_page(url)
            count = count + 1

        del self.product_urls[:]
        self.products = {}

        return results

    def next_page(self):

        self.current_pn = self.current_pn + 1
        if self.api is None:
            self.api = re.sub(r"\?.*$", "", self.keyword)
            # self.api = self.keyword
            self.keyword = None

        if self.current_pn == 1:
            url = self.api
        elif 'productlist' in self.api:
            url = re.sub(r'productlist.*\.html', 'productlist-' + str(self.current_pn)+'.html', self.api)
        elif 'productgrouplist' in self.api:
            url = re.sub(r'(productgrouplist-\d+)(-\d*)?', r'\1-' + str(self.current_pn), self.api)

        msg = {'type':'primary'}
        msg['content'] = '正在抓取产品列表，第'+str(self.current_pn)+'页，网址：'+url
        self.socket.emit('notify', msg, namespace='/markets', room=self.sid)

        self.browser.get(url)
        sl_last_product_img = '#products-container ul:last-child li.last-product .product-img img'
        sl_uls = '#products-container ul'
        # actions = ActionChains(self.browser)
        for ul in self.browser.find_elements(*(By.CSS_SELECTOR, sl_uls)):
            # actions.move_to_element(ul).perform()
            self.browser.execute_script("arguments[0].scrollIntoView();", ul)

        # last_product_img = self.browser.find_element(*(By.CSS_SELECTOR, sl_last_product_img))
        # wait = WebDriverWait(self.browser, 30)
        # wait.until(images_loaded(last_product_img))
            
    def crawl_product_page(self, url):
        try:
            metaTag = self.browser.find_element_by_xpath(self.xp_keywords)
        except NoSuchElementException:
            metaTag = None

        if metaTag is not None:
            tags = self.products[url]['keywords']
            content = metaTag.get_attribute("content")
            title = self.products[url]['title']

            content = re.sub(title+',', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\.,', '-', content)
            for word in content.split(','):
                word = re.sub('-', '.,', word).strip()
                tags.append(word)

class images_loaded(object):
    def __init__(self, element):
        self.element = element
    def __call__(self, driver):
        if 'loading.gif' in self.element.get_attribute("src"):
            return False
        else:
            return self.element
        