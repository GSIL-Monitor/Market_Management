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
import html
import time
import re
import traceback

class Alibaba:
    api = 'https://i.alibaba.com'
    api_post_similar_product = 'https://hz-productposting.alibaba.com/product/post_product_interface.htm?from=manage&import_product_id='
    api_product_manage = 'https://hz-productposting.alibaba.com/product/products_manage.htm'

    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--ignore-certificate-errors')

    def __init__(self, user, password, socketio=None, namespace=None, room=None):
        self.user = user
        self.password = password
        self.socketio = socketio
        self.namespace = namespace
        self.room = room
        self.browser = webdriver.Chrome(chrome_options=self.chrome_options)

    def notify(self, typo, message):
        if self.socketio:
            if '_' in typo:
                self.socketio.emit(typo, message, namespace=self.namespace, room=self.room)
            else:
                self.socketio.emit('notify', dict(type=typo, content=message), namespace=self.namespace, room=self.room)
        else:
            print(typo, message)

    def login(self):
        a_signout = self.browser.find_elements_by_css_selector('header a[data-val="ma_signout"]')
        span_wel = self.browser.find_elements_by_css_selector(
            'header div[data-role="user"] div[data-role="wel"] a span')
        if len(span_wel) != 0 or len(a_signout) != 0:
            if len(span_wel) != 0:
                self.notify("warning", "已经登录为: " + span_wel[0].get_attribute('innerHTML'))
            if len(a_signout) != 0:
                ln = self.browser.find_elements_by_css_selector('header div.sc-hd-ms-name')
                ln = ln[0].get_attribute('innerHTML')
                self.notify("warning", "已经登录为: " + re.sub('Hi +', '', ln))
            return

        try:
            if self.api not in self.browser.current_url:
                self.notify("primary", "打开网址：" + self.api)
                self.browser.get(self.api)
                pan_wel = self.browser.find_elements_by_css_selector(
                    'header div[data-role="user"] div[data-role="wel"] a span')
                if len(span_wel) != 0:
                    self.notify('warning', "已经登录为: " + span_wel.get_attribute('innerHTML'))
                    return

        except (WebDriverException, ConnectionAbortedError, AttributeError):
            self.notify("primary", "打开网址：" + self.api)
            self.browser.get(self.api)

        try:
            self.notify("primary", "等待登陆页面加载 ... ...")
            WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#alibaba-login-iframe iframe")))
            time.sleep(1)

            windows = self.browser.window_handles
            win = self.browser.current_window_handle
            for window in windows:
                if window != win:
                    self.browser.switch_to.window(window)
                    self.browser.close()
            self.browser.switch_to.window(win)

            iframe = self.browser.find_element_by_css_selector('#alibaba-login-iframe iframe')
            self.browser.switch_to.frame(iframe)

            self.notify("primary", "输入登录信息， 并登录")
            input_login = self.browser.find_element_by_css_selector('input#fm-login-id')
            input_pwd = self.browser.find_element_by_css_selector('input#fm-login-password')
            input_submit = self.browser.find_element_by_css_selector('input#fm-login-submit')
            input_login.clear()
            input_pwd.clear()
            input_login.send_keys(self.user)
            input_pwd.send_keys(self.password)
            input_submit.click()

            WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'header div[data-role="user"]')))
            span = self.browser.find_element_by_css_selector(
                'header div[data-role="user"] div[data-role="wel"] a span')
            user_name = span.get_attribute('innerHTML')
            self.notify("success", "成功 登录 阿里巴巴 国际站！用户名：" + user_name)
        except TimeoutException:
            self.notify("danger", "登录 阿里巴巴 国际站 失败！原因超时")

    def crawl_product_data(self, result_message, ali_id):
        api = 'https://hz-productposting.alibaba.com/product/editing.htm?id='
        browser = self.browser
        if not browser:
            self.notify("danger", "没有登录，请先登录")
            return
        attrs = {'alibaba_id': ali_id}
        template = {}
        try:
            self.notify("primary", "打开产品 [" + ali_id + "] 编辑页面 ... ...")
            browser.get(api + ali_id)
            WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#editor-container')))

            self.notify("primary", "开始爬取产品 [" + ali_id + "] 数据 ... ...")
            attrs['alibaba_category'] = browser.find_element_by_css_selector('span#cate-path-text-copy').text.strip()
            attrs['name'] = browser.find_element_by_css_selector('input#productName').get_attribute('value').strip()
            keywords = []
            keyword = browser.find_element_by_css_selector('input#productKeyword').get_attribute('value').strip()
            keywords.append(keyword)
            keyword = browser.find_element_by_css_selector('input#keywords2').get_attribute('value').strip()
            keywords.append(keyword)
            keyword = browser.find_element_by_css_selector('input#keywords3').get_attribute('value').strip()
            keywords.append(keyword)
            attrs['keywords'] = keywords
            attrs['type'] = browser.find_element_by_css_selector(
                '#productAttribute>div:first-child>div>input').get_attribute('value').strip()
            attrs['brand'] = browser.find_element_by_css_selector(
                '#productAttribute>div:nth-child(2)>div>input').get_attribute('value').strip()

            origin = []
            select = Select(browser.find_elements_by_css_selector('#productAttribute>div:nth-child(3) select')[0])
            origin.append(select.first_selected_option.text)

            select = Select(browser.find_elements_by_css_selector('#productAttribute>div:nth-child(3) select')[1])
            origin.append(select.first_selected_option.text)
            attrs['origin'] = origin

            select = Select(browser.find_elements_by_css_selector('#productAttribute>div:nth-child(4) select')[0])
            attrs['material'] = select.first_selected_option.text

            select = Select(browser.find_elements_by_css_selector('#productAttribute>div:nth-child(5) select')[0])
            attrs['production_method'] = select.first_selected_option.text

            custom_attributes = []
            trs = browser.find_elements_by_css_selector('#attr table tr')
            trs.pop(0)
            for tr in trs:
                key = tr.find_elements_by_css_selector('input')[0].get_attribute('value').strip()
                value = tr.find_elements_by_css_selector('input')[1].get_attribute('value').strip()
                custom_attributes.append([key, value])
            attrs['custom_attributes'] = custom_attributes

            browser.find_element_by_css_selector('#mceu_0 button').click()
            WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#mceu_46 textarea')))
            time.sleep(1)
            template['html'] = browser.find_element_by_css_selector('#mceu_46 textarea').get_attribute('value').strip()
            browser.find_element_by_css_selector('#mceu_0 button').click()
            WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#mceu_46 iframe')))
            time.sleep(1)

            css_selector = '#tradInfoblock>div:nth-child(3) .price-scroll-selector input[value="uniform"]'
            element = browser.find_element_by_css_selector(css_selector)
            attrs['isTieredPricing'] = element.is_selected()
            if attrs['isTieredPricing']:
                attrs['sales_unit'] = browser.find_element_by_css_selector('#tradeInfoQuantityUnit').text.strip()
                attrs['currency'] = 'USD'
                tieredPricing = []
                trs = browser.find_elements_by_css_selector('#priceSetter .next-table-body tbody tr')
                for tr in trs:
                    volume = tr.find_elements_by_css_selector('input')[0].get_attribute('value').strip()
                    price = tr.find_elements_by_css_selector('input')[1].get_attribute('value').strip()
                    tieredPricing.append([volume, price])
                attrs['tieredPricing'] = tieredPricing
            else:
                attrs['currency'] = browser.find_element_by_css_selector('#moneyTypeSelect span').text.strip()
                price_range = []
                price_range.append(
                    browser.find_element_by_css_selector('#priceRangeMin').get_attribute('value').strip())
                price_range.append(
                    browser.find_element_by_css_selector('#priceRangeMax').get_attribute('value').strip())
                attrs['price_range'] = price_range
                attrs['sales_unit'] = browser.find_element_by_css_selector('#priceUnitSelect span').text.strip()
                attrs['MOQ'] = browser.find_element_by_css_selector('#minOrderQuantity').get_attribute('value').strip()
                attrs['additional_trading_infomation'] = browser.find_element_by_css_selector(
                    '#minOrderOther').get_attribute('value').strip()
            payment_methods = {}
            checkboxes = browser.find_elements_by_css_selector('.trade-info-payment-group input[type="checkbox"]')
            for cb in checkboxes:
                value = cb.get_attribute('value')
                checked = cb.is_selected()
                if value == "Others":
                    continue
                payment_methods[value] = checked
            attrs['payment_methods'] = payment_methods
            if browser.find_element_by_css_selector('#paymentMethodOther').is_selected():
                attrs['other_payment_method'] = browser.find_element_by_css_selector(
                    '#paymentMethodOtherDesc').get_attribute('value')

            attrs['delivery_time'] = browser.find_element_by_css_selector('#consignmentTerm').get_attribute('value')
            attrs['port'] = browser.find_element_by_css_selector('#port').get_attribute('value')
            supply_ability = []
            supply_ability.append(browser.find_element_by_css_selector('#supplyQuantity').get_attribute('value'))
            select = Select(browser.find_element_by_css_selector('#supplyUnit'))
            supply_ability.append(select.first_selected_option.text)
            select = Select(browser.find_element_by_css_selector('#supplyPeriod'))
            supply_ability.append(select.first_selected_option.text)
            attrs['supply_ability'] = supply_ability
            attrs['additional_delivery_information'] = browser.find_element_by_css_selector(
                '#supplyOther').get_attribute('value')
            attrs['packaging'] = browser.find_element_by_css_selector('#packagingDesc').get_attribute('value')

            self.notify('success', "完成 对产品 [" + ali_id + "] 编辑页面 的数据爬取！")
        except TimeoutException as e:
            attrs = None
            template = None
            msg = "爬取产品 [" + ali_id + '] 数据 出错，超时，' + str(e)
        except NoSuchElementException as e:
            attrs = None
            template = None
            msg = "爬取产品 [" + ali_id + "] 数据 出错，没找到目标元素, " + str(e)
        except Exception as e:
            attrs = None
            template = None
            msg = "爬取产品 [" + ali_id + "] 数据 出错, " + str(e)
            traceback.print_exc()
        finally:
            browser.get('https://i.alibaba.com')

        if not attrs or not template:
            self.notify("danger", msg)
            self.notify(result_message, None)
        else:
            result = {'attributes': attrs, 'template': template}
            self.notify(result_message, result)

    def submit_product(self):
        # submit to next step
        btn_submit_next = self.browser.find_element_by_css_selector('button#submitFormNext')
        ActionChains(self.browser).move_to_element(btn_submit_next).perform()
        btn_submit_next.click()

        # 提交表格
        self.notify("primary", "提交产品")
        btn_submit = WebDriverWait(self.browser, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#submitFormBtnA')))
        btn_submit.click()

        WebDriverWait(self.browser, 30).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '.next-step-item-last.next-step-item-process,.ui2-dialog-transition')))
        # 检查 是否 违规
        if self.browser.find_elements_by_css_selector('.ui2-dialog-transition'):
            words = ''
            for td in self.browser.find_elements_by_css_selector(
                    '.ui2-dialog-transition tr:not(:first-child) td:nth-child(2)'):
                words = words + ' ' + td.text
            self.notify("danger", "出现 违规词 [ " + words + " ], 请手动确认，否则 30 秒后 提交 失败")
            WebDriverWait(self.browser, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.next-step-item-last.next-step-item-process')))

        self.notify("primary", "成功 提交 产品")

    def update_product(self, data):
        browser = self.browser
        try:
            api = 'https://hz-productposting.alibaba.com/product/editing.htm?id='
            ali_id = str(data['ali_id'])
            if not browser:
                self.notify('danger', "没有登录，请先登录")
                return

            self.notify("primary", "打开产品 [" + ali_id + "] 编辑页面 ... ...")
            browser.get(api + ali_id)
            WebDriverWait(browser, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#editor-container')))

            result = False
            if self.update_product_price(data):
                result = True
            if self.update_product_detail_pictures(data):
                result = True

            if result:
                self.submit_product()
        except TimeoutException as e:
            self.notify('error', '更新产品 [' + ali_id + '] 数据 出错，超时，' + str(e))
            traceback.print_exc()
        except NoSuchElementException as e:
            self.notify('error', '更新产品 [' + ali_id + '] 数据 出错，没找到目标元素, ' + str(e))
            traceback.print_exc()
        except Exception as e:
            self.notify('error', '更新产品 [' + ali_id + '] 数据 出错, ' + str(e))
            traceback.print_exc()
        finally:
            pass

    def update_product_price(self, data):
        if 'price' not in data:
            return False
        price = data['price']
        if price['isTieredPricing']:
            self.notify("error", "该功能还没有实现 ... ...")
            return False
        else:
            self.notify("primary", "设置产品 [" + str(data['ali_id']) + "] 的价格区间 ... ...")
            js_templ = "document.querySelector('{selector}').value = '{value}';"
            js = js_templ.format(selector='#priceRangeMin', value=price['price_range'][0])
            self.browser.execute_script(js)
            js = js_templ.format(selector='#priceRangeMax', value=price['price_range'][1])
            self.browser.execute_script(js)
            return True

    def update_product_detail_pictures(self, data):
        result = False
        if 'detail_pictures' not in data:
            return result
        pictures = data['detail_pictures']
        browser = self.browser

        element = browser.find_element_by_css_selector("#editor-container")
        ActionChains(browser).move_to_element(element).perform()
        # self.notify("primary", "开始 设置 产品详情页 ... ...")
        # 点击 详情编辑器 ‘源代码’ 按钮， 清空内容，再切换回 富文本 编辑状态
        browser.find_element_by_css_selector('#mceu_0 button').click()
        textarea = WebDriverWait(browser, 5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#mceu_46 textarea')))

        text = textarea.get_attribute('value')
        soup = BeautifulSoup(text, 'html.parser')
        for img in soup.find_all('img'):
            src = img['src']
            key = re.sub('//[^\.]*\.', '', src)

            for idx, pic in enumerate(pictures):
                if key not in pic['old']:
                    continue

                result = True
                img['src'] = pic['new']
                if img.has_attr('ori-width'):
                    del img['ori-width']
                if img.has_attr('ori-height'):
                    del img['ori-height']
                break

        if result:
            js_templ = "document.querySelector('{selector}').value = '{value}';"
            js = js_templ.format(selector='#mceu_46 textarea', value=re.sub('\n', '\\\\n', str(soup)))
            browser.find_element_by_css_selector('#mceu_46 textarea').clear()
            browser.execute_script(js)
            browser.find_element_by_css_selector('#mceu_0 button').click()
            WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#mceu_46 iframe')))
        return result

    def post_similar_product(self, product, similar_ali_pid):
        browser = self.browser
        js_templ = "document.querySelector('{selector}').value = '{value}';"
        attrs = product['attributes']

        try:
            self.notify("primary", "打开 发布相似产品 网址: " + self.api_post_similar_product + similar_ali_pid)

            browser.get(self.api_post_similar_product + similar_ali_pid)

            css_selector = 'header div[data-role="user"] div[data-role="wel"] a span'
            if len(browser.find_elements_by_css_selector(css_selector)) == 0:
                self.notify("warning", "请先登录 阿里巴巴 国际站")
                return

            WebDriverWait(browser, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#editor-container')))

            self.notify("primary", "修改标题和关键字 ... ...")

            js = js_templ.format(selector='#productName', value=html.escape(attrs['name']))
            browser.execute_script(js)
            js = js_templ.format(selector='#productKeyword', value=html.escape(attrs['keywords'][0]))
            browser.execute_script(js)
            js = js_templ.format(selector='#keywords2', value=html.escape(attrs['keywords'][1]))
            browser.execute_script(js)
            js = js_templ.format(selector='#keywords3', value=html.escape(attrs['keywords'][2]))
            browser.execute_script(js)
            js = js_templ.format(selector='#productAttribute>div:first-child input[type="text"]',
                                 value=html.escape(attrs['type']))
            browser.execute_script(js)

            # 上传 产品 图片
            element = browser.find_element_by_css_selector("#iamge-info-block .image-upload-list")
            ActionChains(browser).move_to_element(element).perform()
            css_selector = '#iamge-info-block .image-upload-list-item-info'
            has_selector = 'image-upload-list-item-done'
            counter = 1
            for file in product['pictures']:
                self.notify("primary", "上传产品图片: 第 " + str(counter) + " 张, " + file.split('\\').pop())
                input_file_list = browser.find_element_by_css_selector('#iamge-info-block input[type="file"]')
                input_file_list.send_keys(file)
                WebDriverWait(browser, 15).until(ElementHasCssClass((By.CSS_SELECTOR, css_selector), has_selector))
                counter += 1

            if len(product['template']['selections']) != 0:
                # 开始 产品详情 设置
                element = browser.find_element_by_css_selector("#editor-container")
                ActionChains(browser).move_to_element(element).perform()
                self.notify("primary", "开始 设置 产品详情页 ... ...")
                # 点击 详情编辑器 ‘源代码’ 按钮， 清空内容，再切换回 富文本 编辑状态
                browser.find_element_by_css_selector('#mceu_0 button').click()
                WebDriverWait(browser, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, '#mceu_46 textarea')))
                browser.find_element_by_css_selector('#mceu_46 textarea').clear()
                browser.find_element_by_css_selector('#mceu_0 button').click()
                WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#mceu_46 iframe')))
                css_selector = '#react-tinymce-0-ali-foot-img'
                WebDriverWait(browser, 15).until(ElementTextEquals((By.CSS_SELECTOR, css_selector), '15'))

                # 点击 ‘从我的电脑选择图片’
                self.notify("primary", "开始 上传 产品详情页 图片 ... ...")
                button_pic_upload = browser.find_element_by_css_selector('#mceu_25 button')
                button_pic_upload.click()
                time.sleep(0.5)
                iframe = WebDriverWait(browser, 15).until(
                    EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, '.mce-reset iframe')))

                # iframe = browser.find_element_by_css_selector('.mce-reset iframe')
                # browser.switch_to.frame(iframe)

                # 上传图片
                css_selector = '#container .next-upload-list .next-upload-list-item'
                has_selector = 'next-upload-list-item-done'
                counter = 0
                for file in product['template_pictures']:
                    self.notify("primary", "上传 产品详情页 图片: 第 " + str(counter) + ' 张, ' + file.split('\\').pop())

                    WebDriverWait(browser, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#container input[type="file"]')))
                    input_file = browser.find_element_by_css_selector('#container input[type="file"]')
                    input_file.send_keys(file)
                    # WebDriverWait(browser, 15).until(element_has_css_class((By.CSS_SELECTOR, css_selector), has_selector))
                    WebDriverWait(browser, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.photobank-action-bar #confirm')))

                    counter += 1

                browser.find_element_by_css_selector('.photobank-action-bar #confirm').click()
                browser.switch_to.default_content()
                text = str(15 - counter)
                css_selector = '#react-tinymce-0-ali-foot-img'
                WebDriverWait(browser, 15).until(ElementTextEquals((By.CSS_SELECTOR, css_selector), text))

                # 获取上传图片的 阿里站 链接
                self.notify("primary", "获取上传图片的 阿里站链接, 并修改模板")
                btn_source = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#mceu_0 button')))
                btn_source.click()
                WebDriverWait(browser, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, '#mceu_46 textarea')))
                imgs_string = browser.find_element_by_css_selector('#mceu_46 textarea').get_attribute('value')
                imgs_soup = BeautifulSoup(imgs_string, 'html.parser')
                templ_imgs = []
                for img in imgs_soup.find_all('img'):
                    fn = img['alt']
                    src = img['src']
                    fn = re.sub('.jpg', '', fn)
                    templ_imgs.append({'fn': fn, 'src': src})
                # 修改 模板 内容
                templ_soup = BeautifulSoup(product['template']['template'], 'html.parser')
                pic_index = 0
                for sel in product['template']['selections']:
                    if sel['type'] == 'title':
                        span = templ_soup.select(sel['selector'])
                        if len(span) == 1:
                            span[0].string = attrs['name']
                        else:
                            msg = "再template中没有找到CSS选择器 " + sel['selector'] + " 所对应的元素"
                            raise NoSuchElementException(msg)
                    elif sel['type'] == 'tag_img':
                        img = templ_soup.select(sel['selector'])
                        if len(img) == 1:
                            img[0]['alt'] = attrs['name']
                            img[0]['src'] = templ_imgs[pic_index]['src']
                            pic_index += 1
                        else:
                            msg = '再template中没有找到CSS选择器 ' + sel['selector'] + ' 所对应的元素'
                            raise NoSuchElementException(msg)
                html_string = str(templ_soup)

                # 修改后的模板输入 textarea
                self.notify("primary", "修改后的模板输入, 注入到详情页中")
                js = js_templ.format(selector='#mceu_46 textarea', value=re.sub('\n', '\\\\n', html_string))
                browser.execute_script(js)
                browser.find_element_by_css_selector('#mceu_0 button').click()
                WebDriverWait(browser, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#mceu_46 iframe')))

            # check free sample
            self.notify("primary", "点选免费样品, 保护产品图片")
            btn_free_sample = browser.find_element_by_css_selector('#rbtnFreeSample')
            ActionChains(browser).move_to_element(btn_free_sample).perform()
            btn_free_sample.click()

            # make product pictures to be protected
            quantity = 6
            css_selector = "#iamge-info-block li.image-upload-list-item .action-wrapper"
            WebDriverWait(browser, 15).until(ElementQuantityEquals((By.CSS_SELECTOR, css_selector), quantity))
            css_selector = "#iamge-info-block li.image-upload-list-item .action-wrapper a"
            while True:
                elements = browser.find_elements_by_css_selector(css_selector)
                found = False
                try:
                    for element in elements:
                        if element.text == '添加守护':
                            found = True
                            element.click()  # exception: element is not clickable
                            break
                except StaleElementReferenceException:
                    time.sleep(0.5)
                    continue
                if not found:
                    break

            self.submit_product()

            return product

        except TimeoutException:
            self.notify("danger", "错误：" + str(TimeoutException))
            return TimeoutException
        except NoSuchElementException:
            self.notify("danger", "错误：" + str(NoSuchElementException))
            return NoSuchElementException

    def get_posted_product_info(self, pn):
        browser = self.browser
        products = []
        try:
            self.notify("primary", '打开 产品管理 页面 ... ...')
            browser.get(self.api_product_manage)
            css_selector = '#ballon-container .list-item'
            WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))

            msg = '切换 至 显示全部产品 ... ...'
            self.notify("primary", msg)
            css_selector = '#ballon-container div[role="tab"]:nth-child(1)'
            tab_all = WebDriverWait(browser, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
            tab_all.click()
            browser.implicitly_wait(1)
            css_selector = '#ballon-container .manage-loading .next-loading-tip'
            div_tip = browser.find_elements_by_css_selector(css_selector)
            if len(div_tip) != 0:
                WebDriverWait(browser, 20).until(EC.staleness_of(div_tip[0]))

            pn = int(pn)
            for counter in range(pn):
                msg = '查找 全部产品列表 第 ' + str(counter + 1) + ' 页'
                self.notify("primary", msg)

                css_selector = '#ballon-container .list-item'
                html_source = browser.page_source
                doc = pq(html_source)
                items = doc('#ballon-container .list-item')
                for item in items:
                    pq_item = pq(item)
                    product = {}
                    pq_a = pq_item.find('.product-subject a')
                    if len(pq_a) == 0:
                        continue

                    product['href'] = pq_a.attr('href')
                    product['title'] = pq_a.text().strip().lower()
                    product['pid'] = pq_item.find('.product-model').text().split(':')[1].strip()
                    product['category'] = pq_item.find('.product-group').text().split(':')[1].strip()
                    product['update'] = pq_item.find('.product-update span').text().strip()
                    product['price'] = pq_item.find('.product-price div').text().strip()
                    product['quality'] = []
                    product['quality'].append(pq_item.find('.product-quality div:nth-child(1)').text().strip())
                    product['quality'].append(pq_item.find('.product-quality div:nth-child(2)').text().strip())
                    pq_tags = pq_item.find('.product-tags .next-tag-body')
                    product['tags'] = []

                    for tag in pq_tags:
                        product['tags'].append(pq(tag).text().strip())

                    result = re.search('id=(\d+)$', product['href'])
                    if result:
                        ali_id = result.group(1)
                    else:
                        ali_id = re.search('_(\d+).htm', product['href']).group(1)
                    product['ali_id'] = ali_id
                    products.append(product)

                if counter == pn - 1:
                    break

                css_selector = '#ballon-container .next-pagination-pages .next'
                btn_next = browser.find_element_by_css_selector(css_selector)
                if btn_next.is_enabled():
                    btn_next.click()
                    browser.implicitly_wait(1)
                    css_selector = '#ballon-container .manage-loading .next-loading-tip'
                    div_tip = browser.find_elements_by_css_selector(css_selector)
                    if len(div_tip) != 0:
                        WebDriverWait(browser, 20).until(EC.staleness_of(div_tip[0]))
                else:
                    break

                self.notify("primary", "完成 查找！")
        except Exception as e:
            self.notify("danger", "爬取产品 [" + ali_id + "] 数据 出错, " + str(e))
            products = None
        finally:
            if self.socketio:
                self.notify("get_posted_product_info_result", products)


class ElementHasCssClass:
    def __init__(self, locator, css_class):
        self.locator = locator
        self.css_class = css_class

    def __call__(self, driver):
        not_found = True
        try:
            elements = driver.find_elements(*self.locator)  # Finding the referenced element
            for element in elements:
                if self.css_class in element.get_attribute("class"):
                    continue
                else:
                    not_found = False
                    break
        except StaleElementReferenceException:
            not_found = True
        finally:
            return not_found


class ElementTextEquals:
    def __init__(self, locator, text):
        self.locator = locator
        self.text = text

    def __call__(self, driver):
        element = driver.find_element(*self.locator)  # Finding the referenced element
        if self.text == element.text:
            return True
        else:
            return False


class ElementQuantityEquals:
    def __init__(self, locator, quantity):
        self.locator = locator
        self.quantity = quantity

    def __call__(self, driver):
        elements = driver.find_elements(*self.locator)  # Finding the referenced element
        print(len(elements), self.quantity)
        if len(elements) == self.quantity:
            return elements
        else:
            return False
