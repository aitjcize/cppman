#-*- coding: utf-8 -*-
# 
# Crawler.py
#
# Copyright (C) 2010 -  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
# All Rights reserved.
#
# This file is part of cppman.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import httplib
import re
import sys

from os.path import join, dirname, normpath
from threading import Thread, Lock
from urllib import quote

class Document(object):
    def __init__(self, res, url):
        self.url = url
        self.query = '' if not '?' in url else url.split('?')[-1]
        self.status = res.status
        self.text = res.read()

class Crawler(object):
    '''
    A Crawler that crawls through cplusplus.com
    '''
    F_ANY, F_SAME_DOMAIN, F_SAME_HOST, F_SAME_PATH = range(4)
    def __init__(self):
        self.host = None
        self.visited = {}
        self.targets = set()
        self.threads = []
        self.concurrency = 0
        self.max_outstanding = 16

        self.follow_mode = self.F_SAME_HOST
        self.content_type_filter = '(text/html)'
        self.url_filters = []
        self.prefix_filter = '^(#|javascript:|mailto:)'

        self.targets_lock = Lock()
        self.concurrency_lock = Lock()
        self.process_lock = Lock()

    def set_content_type_filter(self, cf):
        self.content_type_filter = '(%s)' % ('|'.join(cf))

    def add_url_filter(self, uf):
        self.url_filters.append(uf)

    def set_follow_mode(self, mode):
        if mode > 5:
            raise RuntimeError('invalid follow mode.')
        self.follow_mode = mode

    def set_concurrency_level(self, level):
        self.max_outstanding = level

    def follow_link(self, url, link):
        # Skip prefix
        if re.search(self.prefix_filter, link):
            return None

        # Filter url
        for f in self.url_filters:
            if re.search(f, link):
                return None

        rx = re.match('(https?://)([^/]+)([^\?]*)(\?.*)?', url)
        url_proto = rx.group(1)
        url_host = rx.group(2)
        url_path = rx.group(3) if len(rx.group(3)) > 0 else '/'
        url_dir_path = dirname(url_path)

        rx = re.match('((https?://)([^/]+))?([^\?]*)(\?.*)?', link)
        link_full_url = rx.group(1) != None
        link_proto = rx.group(2) if rx.group(2) else url_proto
        link_host = rx.group(3) if rx.group(3) else url_host
        link_path = quote(rx.group(4)) if rx.group(4) else url_path
        link_query = rx.group(5) if rx.group(5) else ''
        link_dir_path = dirname(link_path)

        if not link_full_url and not link.startswith('/'):
            link_path = normpath(join(url_dir_path, link_path))

        link_url = link_proto + link_host + link_path + link_query

        if self.follow_mode == self.F_ANY:
            return link_url
        elif self.follow_mode == self.F_SAME_DOMAIN:
            return link_url if self.host == link_host else None
        elif self.follow_mode == self.F_SAME_HOST:
            return link_url if self.host == link_host else None
        elif self.follow_mode == self.F_SAME_PATH:
            if self.host == link_host and \
                    link_dir_path.startswith(self.dir_path):
                return link_url
            else:
                return None

    def add_target(self, target):
        if not target:
            return

        self.targets_lock.acquire()
        if self.visited.has_key(target):
            self.targets_lock.release()
            return
        self.targets.add(target)
        self.targets_lock.release()

    def crawl(self, url):
        self.root_url = url

        rx = re.match('(https?://)([^/]+)([^\?]*)(\?.*)?', url)
        self.proto = rx.group(1)
        self.host = rx.group(2)
        self.path = rx.group(3)
        self.dir_path = dirname(self.path)
        self.query = rx.group(4)

        self.targets.add(url)
        self.spawn_new_worker()

        while self.threads:
            try:
                for t in self.threads:
                    t.join(1)
                    if not t.isAlive():
                        self.threads.remove(t)
            except KeyboardInterrupt, e:
                sys.exit(1)

    def spawn_new_worker(self):
        self.concurrency_lock.acquire()
        if self.concurrency >= self.max_outstanding:
            self.concurrency_lock.release()
            return
        self.concurrency += 1
        t = Thread(target=self.worker, args=(self.concurrency,))
        t.daemon = True
        self.threads.append(t)
        t.start()
        self.concurrency_lock.release()

    def worker(self, sid):
        while self.targets:
            try:
                self.targets_lock.acquire()
                url = self.targets.pop()
                self.visited[url] = True
                self.targets_lock.release()

                rx = re.match('https?://([^/]+)(.*)', url)
                host = rx.group(1)
                path = rx.group(2)

                conn = httplib.HTTPConnection(host)
                conn.request('GET', path)
                res = conn.getresponse()

                if res.status == 301 or res.status == 302:
                    rlink = self.follow_link(url, res.getheader('location'))
                    self.add_target(rlink)
                    continue

                # Check content type
                if not re.search(self.content_type_filter,
                        res.getheader('Content-Type')):
                    continue

                doc = Document(res, url)
                self.process_lock.acquire()
                self.process_document(doc)
                self.process_lock.release()

                # Make unique list
                links = re.findall('''href\s*=\s*['"]\s*([^'"]+)['"]''',
                        doc.text, re.S)
                links = list(set(links))

                for link in links:
                    rlink = self.follow_link(url, link.strip())
                    self.add_target(rlink)

                if self.concurrency < self.max_outstanding:
                    self.spawn_new_worker()
            except KeyError as e:
                # Pop from an empty set
                break
            except (httplib.HTTPException, EnvironmentError) as e:
                #print '%s, retrying' % str(e)
                self.targets_lock.acquire()
                self.targets.add(url)
                self.targets_lock.release()

        self.concurrency_lock.acquire()
        self.concurrency -= 1
        self.concurrency_lock.release()

    def process_document(self, doc):
        print 'GET', doc.status, doc.url
