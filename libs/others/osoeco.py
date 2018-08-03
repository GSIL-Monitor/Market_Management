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

class OSOECO:

    @classmethod
    def checkin(cls, browser):
        url = 'https://my.osoeco.xyz'
        lid = 'odingdongo@hotmail.com'
        lpwd = '7758521oness'
        browser.get(url)
        browser.find_element_by_css_selector('#email').send_keys(lid)
        browser.find_element_by_css_selector('#passwd').send_keys(lpwd)
        browser.find_element_by_css_selector('button#login').click()
        try:
            btn_checkin = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#checkin')))
            btn_checkin.click()
        except Exception as e:
            print(e)
            traceback.print_exc()