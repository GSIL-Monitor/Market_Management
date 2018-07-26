from urllib import parse as urlparse
from mitmproxy import http

class ReplaceJs:
    regex = 'assets.alicdn.com/g/secdev/sufei_data/.*/'
    js_file = '.\\libs\\proxy\\index_patched.js'
    js_content = None

    def __init__(self):
        self.load_js_content()

    # def request(self, flow: http.HTTPFlow) -> None:
    #     if 'www.baidu.com' in flow.request.url:
    #         print('--------------------------------------')
    #         us = server = urlparse.parse_qs(urlparse.urlparse(url).query)['upstream'][0]
    #         if flow.live:
    #             flow.live.change_upstream_proxy_server(tuple(us.split(':')))
    #         flow.kill()

    def response(self, flow: http.HTTPFlow) -> None:
        if 'assets.alicdn.com/g/secdev/sufei_data/' in flow.request.url:
            print('======================================')
            self.load_js_content()
            print(flow.request.url, ' was replaced with ', self.js_file)
            flow.response.content = self.js_content

    def load_js_content(self):
        with open(self.js_file, 'r') as file:
            self.js_content = file.read().encode("utf8")


addons = [ReplaceJs()]