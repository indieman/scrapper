#!/usr/bin/env python
#-*- coding: utf-8 -*-

#-*- filename: spider.py -*-

from queue import Queue, Empty 
import threading
import time
import requests
import logging
from urllib.parse import urlparse
from requests.exceptions import ConnectionError
import lxml.html
from lxml.html.clean import Cleaner
import hashlib
import csv

NAME    = "URI Spider"
VERSION = "0.1"
AUTHOR  = "indieman"
LICENSE = "Public domain (FREE)"

count = 0

def spider(thread_number=1, new_proxy=None, url=None):
    
    res_file = csv.writer(open('result.csv', 'w'))
    resFileLock = threading.RLock()
    proxy_lock = threading.RLock()
    pool = Queue()
    threads = []

    pool.put(url)

    for ind in range(int(thread_number)):
        t = Spider(pool, resFileLock, res_file, proxy_lock, new_proxy)
        threads.append(t)
        t.start()
        time.sleep(2)


    while threading.activeCount()>1:
        try:
            pass
        except KeyboardInterrupt:
            print()
            print("Ctrl-c received! Sending kill to threads...")
            for t in threads:
                t.kill_received = True
            return count


class Spider(threading.Thread):
    ip_url = u'https://goffee.herokuapp.com/ip'
    last_ip = None

    urls = set()

    def __init__(self, pool, resFileLock, res_file, proxy_lock, new_proxy):
        self.new_proxy = new_proxy
        threading.Thread.__init__(self)
        self.res_file = res_file
        self.resFileLock = resFileLock
        self.pool = pool
        self.proxy_lock = proxy_lock
        
        self.kill_received = False

    def get(self, url):
        try:
            res = requests.get(url)
            html = lxml.html.fromstring(res.text)
        except Exception as e:
            logging.error(e)
        try:
            cleaner = Cleaner(allow_tags=[''], remove_unknown_tags=False)
            cleaned_text = cleaner.clean_html(res.text)
            hash = hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()
            length = len(cleaned_text.encode('utf-8'))
        except Exception as e:
            logging.error(e)
            html = None
            hash = None
            length = 0
        return (url, html, hash, length)
    
    def get_uri(self, url, html):
        if url is not None and html is not None:
            print(url)
            parsed_uri = urlparse(url)
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            html.make_links_absolute(url)
            for l in html.iterlinks():
                parsed_uri = urlparse(l[2])
                curr_domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                if curr_domain == domain:
                    if l[2] not in self.urls:
                        self.pool.put(l[2])

                    self.urls.add(l[2])
    
    def save(self, results):
        if results:
            self.resFileLock.acquire(True)

            for res in results:
                print(res)
                self.res_file.writerow(res)
            self.resFileLock.release()

    def search(self, html):
        results = list()
        org_element_list = html.find_class('org_full_box')

        if org_element_list:
            org_element = org_element_list.pop()
     
            name = org_element.find_class('org_header')[0].text_content()
            name = ' '.join(name.split())

            org_info = org_element.find_class('orginfo')
            phone = ''
            address = ''
            metro = ''
            area = ''
            site = ''
            email = ''
            time = ''
            category = ''
            services = ''

            for tr in org_info[0]:
                label = tr[0].text_content()
                if u'Телефоны:' == label:
                    phone = tr[1].text_content()
                    phone = ' '.join(phone.split())
                if u'Адрес:' == label:
                    address = tr[1].text_content()
                    address = ' '.join(address.split())
                if u'Метро:' == label:
                    metro = tr[1].text_content()
                    metro = ' '.join(metro.split())
                if u'Район:' == label:
                    area = tr[1].text_content()
                    area = ' '.join(area.split())
                if u'Сайт:' == label:
                    site = tr[1].text_content()
                    site = ' '.join(site.split())
                if u'E-mail:' == label:
                    email = tr[1].text_content()
                    email = ' '.join(email.split())
                if u'Время работы:' == label:
                    time = tr[1].text_content()
                    time = ' '.join(time.split())
                if u'Рубрики:' == label:
                    category = tr[1].text_content()
                    category = ' '.join(category.split())
                if u'Услуги и товары:' == label:
                    services = tr[1].text_content()
                    services = ' '.join(services.split())

            results = [[
                name,
                phone,
                address,
                metro,
                area,
                site,
                email,
                time,
                category,
                services
            ],]
        return results

    def run(self):
        while True:
            try:
                url = self.pool.get(True, 1)
            except Empty:
                break
            self.check_proxy()
            try:
                print(len(self.urls), url)
                (url, html, hash, length) = self.get(url)
                if html is not None:
                    self.get_uri(url, html)
                    results = self.search(html)
                    self.save(results)

                self.pool.task_done()
            except ConnectionError:
                logging.info('Connection Error')
        
    def check_proxy(self):
        global count
        self.proxy_lock.acquire(True)
        count += 1
        while True:
            try:
                if count < 10:
                    break
                else:
                    self.new_proxy()
                while True:
                    time.sleep(0.1)
                    res = requests.get(self.ip_url)
                    if self.last_ip != res.text or not self.last_ip:
                        self.last_ip = res.text
                        count = 0
                        break

            except Exception as e:
                print(e)
                pass
                
        self.proxy_lock.release()
    
