import re
import time
from .keywords_crawler import KewordsCrawler
from selenium.common.exceptions import NoSuchElementException

class KwclrAliSr(KewordsCrawler):
    # browser = None
    # keyword = None
    # socket = None
    # page_quantity = 1
    # current_pn = 0

    api = 'https://www.alibaba.com/showroom/'

    # we_next_page = None
    cl_item = 'div.item-main'
    cl_title = 'div.item-info h2>a'
    cl_keywords = 'div.tags'
    cl_img = 'div.item-main>div.item-img img'
    cl_crown = 'div.item-info h2>i.ui2-icon-crown'
    cl_ad = 'div.item-info h2>div.seo-ad-flag>.sl'

    def crawl(self):
        results = []
        items = self.browser.find_elements_by_css_selector(self.cl_item)
        for item in items:
            result = {'title': "", 'keywords': [], 'img': ""}
            result['title'] = item.find_element_by_css_selector(self.cl_title).get_attribute('title')
            result['href'] = item.find_element_by_css_selector(self.cl_title).get_attribute('href')
            result['img'] = item.find_element_by_css_selector(self.cl_img).get_attribute('src')
            if not result['img']:
                result['img'] = item.find_element_by_css_selector(self.cl_img).get_attribute('data-jssrc')

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

            try:
                tag = item.find_element_by_css_selector(self.cl_keywords)
            except NoSuchElementException:
                tag = None

            if tag is not None:
                tag = tag.get_attribute('innerHTML').replace('Tags:', '')
                counter = 0
                for word in tag.split('|'):
                    if counter == 3:
                        break
                    text = word.strip()
                    m = re.search('<a [^>]*>(.*)</a>', text)
                    if m:
                        kw = m.group(1)
                    else:
                        kw = text

                    if kw.lower() == 'view larger image':
                        break
                    else:
                        result['keywords'].append(kw)

                    counter += 1

            results.append(result)
        return results

    def next_page(self):
        self.current_pn = self.current_pn + 1
        if self.current_pn == 1:
            url = self.api + '-'.join(self.keyword.split(' ')) + '.html'
        else:
            url = self.api + '-'.join(self.keyword.split(' ')) + '_' + str(self.current_pn) + '.html'

        msg = {'type':'primary'}
        msg['content'] = '正在抓取产品列表，第'+str(self.current_pn)+'页，网址：'+url
        if self.socket:
            self.socket.emit('notify', msg, namespace='/markets', room=self.sid)
        else:
            print('notify', msg)

        self.browser.get(url)
        time.sleep(self.wait_seconds)