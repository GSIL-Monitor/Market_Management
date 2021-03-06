from flask import request, session, current_app
from flask_socketio import emit, join_room, leave_room
from .. import socketio
# from .. import scheduler
# from .. import active_tasks as all_tasks
# from .. import schedule_task
# from .. import get_p4p

from libs.CeleryTasks import tasks
from datetime import datetime
from libs.json import JSON
import os
import tkinter
from tkinter import filedialog

import os
import re
import time
import pendulum

from selenium import webdriver

from libs.alibaba.alibaba import Alibaba
from libs.crawlers.keywords_crawler_alibaba import KwclrAlibaba
from libs.crawlers.keywords_crawler_ali_sr import KwclrAliSr
from libs.crawlers.keywords_crawler_ali_sp import KwclrAliSp
from libs.crawlers.keywords_crawler_amazon import KwclrAmazon


@socketio.on('crawl_products_rankings', namespace='/markets')
def crawl_products_rankings(market, keywords):
    socketio.start_background_task(background_task_crawl_products_rankings, keywords, 1, socketio, '/markets', request.sid)

def background_task_crawl_products_rankings(kws, max_processes, socketio, ns, room):
    processes_count = 0
    records = []
    results = {}
    idx_kws = -1
    while True:
        while processes_count < max_processes and (idx_kws+1) < len(kws):
            idx_kws +=1
            kw = kws[idx_kws]
            kwargs={'keyword': kw, 'pages': 5}
            result = tasks.crawl_product_ranking.apply_async(kwargs=kwargs, queue='eyelash_products_ranking')
            results[kw] = result
            processes_count += 1
            
            print(kw, end=',')

        print()
        print('--------------')

        if processes_count == 0:
            break

        new_records = []
        finished_kws = []
        while True:
            for kw in results:
                result = results[kw]
                if result.ready():
                    record = result.get()
                    record['keyword'] = kw
                    new_records.append(record)
                    records.append(record)
                    finished_kws.append(kw)
                    processes_count -= 1
                    
            for kw in finished_kws:
                results.pop(kw)
            if new_records:
                print('finished:', len(new_records), finished_kws)
                socketio.emit('crawl_products_rankings_finished_kws', finished_kws, namespace=ns, room=room)
                break
            else:
                time.sleep(1)
    socketio.emit('crawl_products_rankings_results', records, namespace=ns, room=room)

@socketio.on('get_products_rankings', namespace='/markets')
def get_products_rankings(market, keywords):

    root = market['directory']+'_config'
    products_rankings_dir = root+'//'+'products_ranking'

    products_rankings = []
    for kw in keywords:
        file = products_rankings_dir + '//' + kw + '.json'

        if not os.path.isfile(file):
            continue

        obj = JSON.deserialize(root, 'products_ranking', file)
        obj['keyword'] = kw
        products_rankings.append(obj)
    return products_rankings

@socketio.on('get_visitors', namespace='/markets')
def get_visitors(market, start_date='2018-08-01', end_date=None):

    start = pendulum.parse(start_date)
    if end_date:
        end = pendulum.parse(end_date)
    else:
        end = pendulum.now()

    root = market['directory']+'_config'
    visitor_dir = root+'//'+'visitors'
    files = os.listdir(visitor_dir)

    visitors = []
    for f in files:
        if not f.startswith('visitors_') or not f.endswith('.json'):
            continue

        dt = pendulum.parse(re.search('visitors_(.*).json', f).group(1))
        if start <= dt <= end:
            visitors += JSON.deserialize(root, 'visitors', f)
    return visitors

@socketio.on('get_p4p_keywords_crawl_result_file_list', namespace='/markets')
def get_p4p_keywords_crawl_result_file_list(market):
    root = market['directory'] + '_config'
    if not os.path.exists(root):
        os.makedirs(root)
    return [n for n in os.listdir(root) if os.path.isfile(os.path.join(root, n)) and n.startswith('p4p_keywords_crawl_result_')]


@socketio.on('connect', namespace='/markets')
def connect_products():
    pass


@socketio.on('get_market', namespace='/markets')
def get_market(name):
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if name in markets:
        market = markets[name]
    else:
        market = None
    return market


@socketio.on('update_market', namespace='/markets')
def update_market(market):
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    key = market['name']
    if key in markets:
        markets[key] = market
        JSON.serialize(markets, '.', 'storage', 'markets.json')


@socketio.on('add_market', namespace='/markets')
def add_market():
    root = tkinter.Tk()
    root.withdraw()
    path = filedialog.askdirectory(parent=root, initialdir="/", title='请选择上传产品目录')
    if path:
        name = os.path.basename(path)
        path = path.replace('/', '\\')
        market = {'name': name, 'directory': path}
        markets = current_app.data.markets

        if market['name'] not in markets:
            markets[market['name']] = market
            JSON.serialize(markets, '.', 'storage', 'markets.json')
            return market
        else:
            msg = {'type': 'warning', 'content': 'The Market of '+market.name+' was already in system!'}
            emit('notify', msg, room=request.sid)
            return
    else:
        msg = {'type': 'primary', 'content': 'No directory of market was selected.'}
        emit('notify', msg, room=request.sid)
        return

@socketio.on('get_all_markets', namespace='/markets')
def get_all_markets():
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if not markets:
        markets = {}
    return markets


@socketio.on('get_categories', namespace='/markets')
def get_categories(market):
    directory = market['directory']
    categories = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    sub_categories = {}
    for cat in categories:
        folder = os.path.join(directory, cat)
        sub_dirs = [n for n in os.listdir(folder) if os.path.isdir(os.path.join(folder, n))]
        sub_cat = []
        for name in sub_dirs:
            sub_folder = os.path.join(folder, name)
            ssub_folders = [n for n in os.listdir(sub_folder) if not name.lower().endswith(' serie') and os.path.isdir(os.path.join(sub_folder, n))]
            if(len(ssub_folders)>0):
                sub_cat.append(name)
        if(len(sub_cat)>0):
            sub_categories[cat] = sub_cat
    
    return {'categories': categories, 'sub_categories':sub_categories}


@socketio.on('remove_market', namespace='/markets')
def remove_market(market):
    markets = JSON.deserialize('.', 'storage', 'markets.json')
    if market['name'] in markets:
        del markets[market['name']]
        JSON.serialize(markets, '.', 'storage', 'markets.json')
        return True
    else:
        msg = {'type':'warning', 'content': 'Market ' + market['name'] + ' was not found. Try Refesh Your Browser!'}
        emit('notify', msg, room=request.sid)
        return False


@socketio.on('get_p4p_records', namespace='/markets')
def get_p4p_records(market, paths, date_str):
    fn_keywords = 'p4p_keywords_crawl_result_' + date_str + '.json.gz'
    fn_balance = 'p4p_balance_change_history_'+date_str+'.json.gz'
    keywords = deserialize(market, paths, fn_keywords, True)
    balance = deserialize(market, paths, fn_balance, True)
    return [keywords, balance]


@socketio.on('serialize', namespace='/markets')
def serialize(obj, market, paths, filename):
    root = market['directory']+'_config'
    JSON.serialize(obj, root, paths, filename)
    return


@socketio.on('deserialize', namespace='/markets')
def deserialize(market, paths, filename, shallow=False):
    root = (market['directory']+'_config')

    if shallow:
        return JSON.deserialize(root, paths, filename)

    objects = []
    while True:
        objects.append(JSON.deserialize(root, paths[:], filename))

        if len(paths) == 0:
            break

        if len(paths) and paths[-1].lower().endswith(' serie') and '_' in filename:
            filename = filename.split('_')[1]
        else:
            paths.pop()

    return objects


@socketio.on('get_file_list', namespace='/markets')
def get_file_list(market, paths):
    root = market['directory']
    path = os.path.join(root, *paths)
    return [n for n in os.listdir(path) if os.path.isfile(os.path.join(path, n))]


@socketio.on('get_products', namespace='/markets')
def get_products(market, paths):
    root = market['directory']
    path = os.path.join(root, *paths)
    folders = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    files = {}
    for folder in folders:
        files[folder] = os.listdir(os.path.join(path, folder))

    attrs = {}
    root_config = (market['directory']+'_config')
    path_config = os.path.join(root_config, *paths)
    if os.path.exists(path_config):
        folders_config = os.listdir(path_config)
        for folder in folders_config:
            if not os.path.exists(os.path.join(path_config, folder)):
                continue
            if os.path.isfile(os.path.join(path_config, folder)):
                continue
            files_config = os.listdir(os.path.join(path_config, folder))
            for file in files_config:
                if not file.endswith('_attributes.json'):
                    continue
                pid = file.split('_')[0]
                ps = paths[:]
                ps.append(folder)
                attrs[folder+'_'+pid] = JSON.deserialize(root_config, ps, file)

    return dict(folders=folders, files=files, attributes=attrs)


@socketio.on('login_alibaba', namespace='/markets')
def login_alibaba(lid, lpwd):
    alibaba = current_app.data.alibaba
    if not alibaba:
        conn = [socketio, '/markets', request.sid]
        alibaba = Alibaba(lid, lpwd, socketio_connection=conn)
        current_app.data.alibaba = alibaba
        socketio.start_background_task(alibaba.login)


@socketio.on('post_similar_products', namespace='/markets')
def post_similar_products(products, similar_product_id):
    alibaba = current_app.data.alibaba
    alibaba.room = request.sid
    socketio.start_background_task(backgound_post_similar_products, alibaba, products, similar_product_id)


def backgound_post_similar_products(alibaba, products, similar_product_id):
    start = time.time()
    counter = 0
    for product in products:
        spid = similar_product_id
        if not similar_product_id:
            spid = product['similar_ali_id']

        if not spid:
            msg = {'type': "danger", 'content': "不能确定 相似产品的 阿里 ID"}
            socketio.emit('notify', msg, namespace=alibaba.namespace, room=alibaba.room)
            return

        result = alibaba.post_similar_product(product, spid)

        if isinstance(result, Exception):
            print(result)

        else:
            print('===============================================================')
            print(alibaba.namespace, alibaba.room)
            print(result)
            socketio.emit('product_posting', result, namespace=alibaba.namespace, broadcast=True, include_self=True)
        counter += 1

        socketio.emit('product_posting_finished', namespace=alibaba.namespace, room=alibaba.room)
    end = time.time()
    total = end - start
    hour = total//3600
    minu = (total%3600)//60
    sec = total - hour * 3600 - minu * 60

    msg = {'type': "primary",
           'content': "共发布 " + str(counter) + " 款产品，用时 " + str(hour) + "小时 " + str(minu) + "分 " + str(
               sec) + "秒，平均：" + str(round(total / counter, 2)) + "秒"}
    socketio.emit('notify', msg, namespace=alibaba.namespace, room=alibaba.room)


@socketio.on('crawl_product_data_from_alibaba', namespace='/markets')
def crawl_product_data_from_alibaba(ali_id):
    result_message = 'crawl_product_data_from_alibaba_result'
    alibaba = current_app.data.alibaba
    alibaba.room = request.sid
    socketio.start_background_task(alibaba.crawl_product_data, result_message, ali_id)


@socketio.on('get_posted_product_info', namespace='/markets')
def get_posted_product_info(page_quantity):
    alibaba = current_app.data.alibaba
    alibaba.room = request.sid
    socketio.start_background_task(alibaba.get_posted_product_info, page_quantity)


@socketio.on('get_products_data', namespace='/markets')
def get_products_data(market, products):
    for p in products:
        paths = p['categories'][:]
        paths.append(p['folder'])
        p['attributes_list'] = deserialize(market, paths[:], p['pid']+'_attributes.json')
        p['template_list'] = deserialize(market, paths[:], p['pid']+'_template.json')
    return products


@socketio.on('reserve_title', namespace='/markets')
def reserve_title(title, product, market):
    mutex = current_app.data.reserve_title_mutex
    with mutex:
        result = {}

        reserved_titles = deserialize(market, [], 'reserved_titles.json', True)
        if reserved_titles is None:
            reserved_titles = {}

        if title in reserved_titles:
            result['success'] = False
            result['product'] = reserved_titles[title]
        else:
            reserved_titles[title] = product
            result['success'] = True
            serialize(reserved_titles, market, [], 'reserved_titles.json')
            socketio.emit('title_reserved', {'title': title, 'product': product, 'market': market}, namespace='/markets', broadcast=True, include_self=True)

    return result


@socketio.on('is_title_reserved', namespace='/markets')
def is_title_reserved(title, market):

    mutex = current_app.data.reserve_title_mutex
    with mutex:
        result = {}

        reserved_titles = deserialize(market, [], 'reserved_titles.json', True)
        if reserved_titles is None:
            reserved_titles = {}

        if title in reserved_titles:
            result['success'] = False
            result['product'] = reserved_titles[title]
        else:
            # reserved_titles[title] = product
            result['success'] = True
            # serialize(reserved_titles, market, [], 'reserved_titles.json')

    return result


@socketio.on('update_products', namespace='/markets')
def update_products(objects):
    alibaba = current_app.data.alibaba
    alibaba.room = request.sid
    socketio.start_background_task(background_update_products, alibaba, objects)

def background_update_products(alibaba, objects):
    for idx, obj in enumerate(objects):
        alibaba.update_product(obj)

@socketio.on('crawl_keywords', namespace='/markets')
def crawl_keywords(keyword, website, page_quantity, market):
    socketio.start_background_task(backgound_crawling_keywords, keyword, website, page_quantity, request.sid, socketio, market)

def backgound_crawling_keywords(keyword, website, page_quantity, sid, socketio, market):
    filename = 'keywords.json'
    root = market['directory'] + '_config'

    msg = {'type': "primary", 'content': "打开浏览器 ... ..."}
    socketio.emit('notify', msg, namespace='/markets', room=sid)

    chrome_options = webdriver.ChromeOptions()
    # chrome_options_headless.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--ignore-certificate-errors')
    browser = webdriver.Chrome(chrome_options=chrome_options)

    if website == 'alibaba':
        crawler_name = re.sub(' ', '_', keyword) + ' - ' + str(page_quantity) + '页 - 阿里'
        crawler = KwclrAlibaba(browser, keyword, page_quantity, sid, socketio)
    if website == 'alibaba_sp':
        supplier = re.search('https:\/\/([^\.]+)', keyword).group(1)
        category = 'all_products'
        if 'productgrouplist' in keyword:
            category = re.search('\/([^\/]+.html)', keyword).group(1)
        crawler_name = supplier + ' - ' + category + ' - ' + str(page_quantity) + '页 - 阿里(商家)'
        crawler = KwclrAliSp(browser, keyword, page_quantity, sid, socketio)
    if website == 'alibaba_sr':
        crawler_name = re.sub( '', '_', keyword) + ' - ' + str(page_quantity) + '页 - 阿里(橱窗)'
        crawler = KwclrAliSr(browser, keyword, page_quantity, sid, socketio)
    if website == 'amazon':
        crawler_name = re.sub(' ', '_', keyword) + ' - ' + str(page_quantity) + '页 - Amazon'
        crawler = KwclrAmazon(browser, keyword, page_quantity, sid, socketio)

    msg = {'type': 'primary', 'content': "开始爬取 ... ..."}
    socketio.emit('notify', msg, namespace='/markets', room=sid)

    result = crawler.start()

    msg = {'type': "primary", 'content': "爬取结束，关闭浏览器 ... ..."}
    socketio.emit('notify', msg, namespace='/markets', room=sid)
    browser.quit()

    msg = {'type': "primary", 'content': "保存结果 ... ..."}
    socketio.emit('notify', msg, namespace='/markets', room=sid)
    obj = JSON.deserialize(root, [], filename)
    if not obj:
        obj = {}
    obj[crawler_name] = result
    JSON.serialize(obj, root, [], filename)

    socketio.emit('keyword_crawling_result', {'key': crawler_name, 'result': result}, namespace='/markets', room=sid)
    browser.quit()

@socketio.on('refresh_p4p_keywords', namespace='/markets')
def refresh_p4p_keywords(market):
    socketio.start_background_task(background_task_refresh_p4p_keywords, market, socketio, '/markets', request.sid)

def background_task_refresh_p4p_keywords(market, socketio, ns, room):
    p4p = get_p4p(market, socketio, room)
    keywords = p4p.crawl_keywords()
    socketio.emit('refresh_p4p_keywords_result', keywords, namespace=ns, room=room)
