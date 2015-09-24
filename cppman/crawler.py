# -*- coding: utf-8 -*-
#
# crawler.py
#
# Copyright (C) 2010 - 2015  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
# All Rights reserved.
#
# This file is part of cppman.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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



import http.client
import os
import re
import sys

from threading import Thread, Lock
from urllib.parse import quote


class Document(object):
    def __init__(self, res, url):
        self.url = url
        self.query = '' if '?' not in url else url.split('?')[-1]
        self.status = res.status
        self.text = res.read().decode()
        self.headers = dict(res.getheaders())


class Crawler(object):
    F_ANY, F_SAME_DOMAIN, F_SAME_HOST, F_SAME_PATH = list(range(4))

    def __init__(self):
        self.host = None
        self.visited = {}
        self.targets = set()
        self.threads = []
        self.concurrency = 0
        self.max_outstanding = 16
        self.max_depth = 0
        self.include_hashtag = False

        self.follow_mode = self.F_SAME_HOST
        self.content_type_filter = '(text/html)'
        self.url_filters = []
        self.prefix_filter = '^(#|javascript:|mailto:)'

        self.targets_lock = Lock()
        self.concurrency_lock = Lock()

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

    def set_max_depth(self, max_depth):
        self.max_depth = max_depth

    def set_include_hashtag(self, include):
        self.include_hashtag = include

    def process_document(self, doc):
        print('GET', doc.status, doc.url)
        # to do stuff with url depth use self._calc_depth(doc.url)

    def crawl(self, url, path=None):
        self.root_url = url

        rx = re.match('(https?://)([^/]+)([^\?]*)(\?.*)?', url)
        self.proto = rx.group(1)
        self.host = rx.group(2)
        self.path = rx.group(3)
        self.dir_path = os.path.dirname(self.path)
        self.query = rx.group(4)

        if path:
            self.dir_path = path

        self.targets.add(url)
        self._spawn_new_worker()

        while self.threads:
            try:
                for t in self.threads:
                    t.join(1)
                    if not t.isAlive():
                        self.threads.remove(t)
            except KeyboardInterrupt:
                sys.exit(1)

    def _url_domain(self, host):
        parts = host.split('.')
        if len(parts) <= 2:
            return host
        elif re.match('^[0-9]+(?:\.[0-9]+){3}$', host):  # IP
            return host
        else:
            return '.'.join(parts[1:])

    def _follow_link(self, url, link):
        # Skip prefix
        if re.search(self.prefix_filter, link):
            return None

        # Filter url
        for f in self.url_filters:
            if re.search(f, link):
                return None

        if not self.include_hashtag:
            link = re.sub(r'(%23|#).*$', '', link)

        rx = re.match('(https?://)([^/:]+)(:[0-9]+)?([^\?]*)(\?.*)?', url)
        url_proto = rx.group(1)
        url_host = rx.group(2)
        url_port = rx.group(3) if rx.group(3) else ''
        url_path = rx.group(4) if len(rx.group(4)) > 0 else '/'
        url_dir_path = os.path.dirname(url_path)

        rx = re.match('((https?://)([^/:]+)(:[0-9]+)?)?([^\?]*)(\?.*)?', link)
        link_full_url = rx.group(1) is not None
        link_proto = rx.group(2) if rx.group(2) else url_proto
        link_host = rx.group(3) if rx.group(3) else url_host
        link_port = rx.group(4) if rx.group(4) else url_port
        link_path = quote(rx.group(5), '/%') if rx.group(5) else url_path
        link_query = quote(rx.group(6), '?=&%') if rx.group(6) else ''
        link_dir_path = os.path.dirname(link_path)

        if not link_full_url and not link.startswith('/'):
            link_path = os.path.normpath(os.path.join(url_dir_path, link_path))

        link_url = link_proto + link_host + link_port + link_path + link_query

        if self.follow_mode == self.F_ANY:
            return link_url
        elif self.follow_mode == self.F_SAME_DOMAIN:
            return link_url if self._url_domain(self.host) == \
                self._url_domain(link_host) else None
        elif self.follow_mode == self.F_SAME_HOST:
            return link_url if self.host == link_host else None
        elif self.follow_mode == self.F_SAME_PATH:
            if self.host == link_host and \
                    link_dir_path.startswith(self.dir_path):
                return link_url
            else:
                return None

    def _calc_depth(self, url):
        # calculate url depth
        return len(url.replace('https', 'http').replace(
            self.root_url, '').rstrip('/').split('/')) - 1

    def _add_target(self, target):
        if not target:
            return

        if self.max_depth and self._calc_depth(target) > self.max_depth:
            return

        self.targets_lock.acquire()
        if target in self.visited:
            self.targets_lock.release()
            return
        self.targets.add(target)
        self.targets_lock.release()

    def _spawn_new_worker(self):
        self.concurrency_lock.acquire()
        self.concurrency += 1
        t = Thread(target=self._worker, args=(self.concurrency,))
        t.daemon = True
        self.threads.append(t)
        t.start()
        self.concurrency_lock.release()

    def _worker(self, sid):
        while self.targets:
            try:
                self.targets_lock.acquire()
                url = self.targets.pop()
                self.visited[url] = True
                self.targets_lock.release()

                rx = re.match('https?://([^/]+)(.*)', url)
                host = rx.group(1)
                path = rx.group(2)

                conn = http.client.HTTPConnection(host, timeout=10)
                conn.request('GET', path)
                res = conn.getresponse()

                if res.status == 301 or res.status == 302:
                    rlink = self._follow_link(url, res.getheader('location'))
                    self._add_target(rlink)
                    continue

                # Check content type
                try:
                    if not re.search(
                        self.content_type_filter,
                            res.getheader('Content-Type')):
                        continue
                except TypeError:  # getheader result is None
                    continue

                doc = Document(res, url)
                self.process_document(doc)

                # Make unique list
                links = re.findall(
                    '''href\s*=\s*['"]\s*([^'"]+)['"]''', doc.text, re.S)
                links = list(set(links))

                for link in links:
                    rlink = self._follow_link(url, link.strip())
                    self._add_target(rlink)

                if self.concurrency < self.max_outstanding:
                    self._spawn_new_worker()
            except KeyError:
                # Pop from an empty set
                break
            except (http.client.HTTPException, EnvironmentError):
                # print('%s, retrying' % str(e))
                self.targets_lock.acquire()
                self.targets.add(url)
                self.targets_lock.release()

        self.concurrency_lock.acquire()
        self.concurrency -= 1
        self.concurrency_lock.release()
