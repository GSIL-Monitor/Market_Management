import re
import time
from .keywords_crawler import KewordsCrawler
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

class KwclrAlibaba(KewordsCrawler):
    # browser = None
    # keyword = None
    # socket = None
    # page_quantity = 1
    # current_pn = 0

    api = 'https://www.alibaba.com/products/'

    # we_next_page = None
    # cl_max_pn = '#site_content div.ui-pagination-pager label'
    cl_item = 'div.m-product-item div.item-content'
    cl_title = 'div.img-wrap img, .img-container img'
    cl_href = 'div.img-wrap a, .img-container a'
    xp_keywords = '//meta[@name="keywords"]'
    cl_img = cl_title
    cl_crown = 'div.title-wrap>i.ui2-icon-crown'
    cl_ad = 'div.item-action span.sl i.ui2-icon-arrow-left'

    products = {}
    product_urls = []

    def crawl(self):
        results = []
        
        # try:
        #     label = self.browser.find_element_by_css_selector(self.cl_max_pn)
        # except NoSuchElementException:
        #     pass
        # self.max_pn = int(label.text.strip().split(' ')[2])
        
        items = self.browser.find_elements_by_css_selector(self.cl_item)
        for item in items:
            result = {'title': "", 'keywords': [], 'img': ""}
            result['title'] = item.find_element_by_css_selector(self.cl_title).get_attribute('alt')
            href = item.find_element_by_css_selector(self.cl_href).get_attribute('href')
            href = re.sub('.html?.*', '.html', href)
            result['href'] = href
            result['img'] = item.find_element_by_css_selector(self.cl_img).get_attribute('src')

            result['isCrowned'] = False
            result['isAd'] = False

            try:
                item.find_element_by_css_selector(self.cl_crown)
                result['isCrowned'] = True
            except NoSuchElementException:
                result['isCrowned'] = False

            try:
                item.find_element_by_css_selector(self.cl_ad)
                result['isAd'] = True
            except NoSuchElementException:
                result['isAd'] = False

            self.product_urls.append(href)
            self.products[href] = result
            results.append(result)


        count = 1
        for url in self.product_urls:
            msg = {'type':'primary'}
            msg['content'] = '正在抓取产品列表，第'+str(self.current_pn)+'页，第'+str(count)+'个产品详情页，网址：'+url
            if self.socket:
                self.socket.emit('notify', msg, namespace='/markets', room=self.sid)
            else:
                print('notify', msg)

            self.browser.get(url)
            # time.sleep(1)
            self.crawl_product_page(url)
            count = count + 1

        del self.product_urls[:]
        self.products = {}

        return results

    def next_page(self):

        self.current_pn = self.current_pn + 1

        if self.current_pn == 1:
            url = self.api + '_'.join(self.keyword.split(' ')) + '.html'
        else:
            url = self.api + '_'.join(self.keyword.split(' ')) + '/' + str(self.current_pn) + '.html'

        msg = {'type':'primary'}
        msg['content'] = '正在抓取产品列表，第'+str(self.current_pn)+'页，网址：'+url
        if self.socket:
            self.socket.emit('notify', msg, namespace='/markets', room=self.sid)
        else:
            print('notify', msg)

        self.browser.get(url)
        
        cl_items = 'div.m-product-item'
        # actions = ActionChains(self.browser)
        for item in self.browser.find_elements(*(By.CSS_SELECTOR, cl_items)):
            # actions.move_to_element(item).perform()
            self.browser.execute_script("arguments[0].scrollIntoView();", item)
            time.sleep(0.05)
        # sl_last_product_img = '#products-container ul:last-child li.last-product .product-img img'
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

            title = re.sub('[ ]*,[ ]*', ', ', title)
            content = re.sub('[ ]*,[ ]*', ', ', content)

            title = re.sub('[()]', ' ', title)
            content = re.sub('[()]', ' ', content)

            try:
                content = re.sub(title+',', '', content, flags=re.IGNORECASE)
            except Exception as e:
                pass

            content = re.sub(r'\.,', '-', content)
            for word in content.split(','):
                word = re.sub('-', '.,', word).strip()
                tags.append(word)
                if len(tags) > 3:
                    tags.pop(0)

class images_loaded(object):
    def __init__(self, element):
        self.element = element
    def __call__(self, driver):
        if 'loading.gif' in self.element.get_attribute("src"):
            return False
        else:
            return self.element
        