class KewordsCrawler:
    browser = None
    keyword = None
    sid = None
    socket = None
    page_quantity = 1
    max_pn = 50
    current_pn = 0
    wait_seconds = 1

    api = None
    we_next_page = None
    cl_title = None
    cl_keywords = None

    def __init__(self, browser, keyword, page_quantity=1, sid=None, socket=None):
        self.browser = browser
        self.keyword = keyword
        self.page_quantity = int(page_quantity)
        self.sid = sid
        self.socket = socket

    def reset(self, keyword, page_quantity=1):
        self.current_pn = 0
        self.keyword = keyword
        self.page_quantity = int(page_quantity)

    def start(self):
        results = []
        for i in range(self.page_quantity):
            self.next_page()
            result = self.crawl()
            results.append(result)

            if self.current_pn == self.max_pn:
                break
        return results

    def crawl(self):
        print('crawl, not yet implented!')
        pass

    def next_page(self):
        print('next_page, not yet implented!')
        pass
