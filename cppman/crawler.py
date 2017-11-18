# -*- coding: utf-8 -*-
#
# crawler.py
#
# Copyright (C) 2010 - 2016  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
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

from __future__ import print_function

import os
import re
import sys

from threading import Thread, Lock

if sys.version_info < (3, 0):
    import httplib

    from urllib import quote
else:
    import http.client as httplib
    from urllib.parse import quote


class Document(object):
    def __init__(self, res, url):
        self.url = url
        self.query = '' if '?' not in url else url.split('?')[-1]
        self.status = res.status
        self.text = res.read()
        self.headers = dict(res.getheaders())

        if sys.version_info >= (3, 0):
            self.text = self.text.decode()

class Link(object):
    def __init__(self, url, std):
        self.url = url
        self.std = std

    def __eq__(self, other):
        return self.url == other.url

    def __hash__(self):
        return self.url.__hash__()

class LinkParser(object):
    def get_unique_links(self, text):
        self.text = text
        links = self._find_links()
        return list(set(links))

class CPlusPlusLinkParser(LinkParser):
    def _find_links(self):
        links = []
        for url, text in re.findall(
            '''<a[^>]*href\s*=\s*['"]\s*([^'"]+)['"][^>]*>(.+?)</a>''', self.text, re.S):
            if re.search('''class\s*=\s*['"][^'"]*C_cpp11[^'"]*['"]''', text):
                links.append(Link(url, "C++11"))
            else:
                links.append(Link(url, ""))
        return links

class CPPReferenceLinkParser(LinkParser):
    def _find_links(self):
        processed = {}
        links = []
        body = re.search('<[^>]*body[^>]*>(.+?)</body>', self.text, re.S).group(1)
        """
        The link follow by the span.t-mark-rev will contained c++xx information.
        Consider the below case
          <a href="LinkA">LinkA</a>
          <a href="LinkB">LinkB</a>
          <span class="t-mark-rev">(C++11)</span>
        We're reversing the body so it is easier to write the regex to get the pair of (std, url).
        """
        bodyr = body[::-1]
        href = "href"[::-1]
        span = "span"[::-1]
        mark_rev = "t-mark-rev"[::-1]
        _class = "class"[::-1]
        for std, url in re.findall(
            '>' + span + '/<\)([^(<>]*)\(' + '>[^<]*?' +
            '''['"][^'"]*''' + mark_rev + '''[^'"]*['"]\s*=\s*''' + _class +
            '[^<]*' + span + '''<.*?['"]([^'"]+)['"]=''' + href
            , bodyr):
            std = std[::-1]
            url = url[::-1]
            links.append(Link(url, std))
            processed[url] = True


        for url in re.findall('''href\s*=\s*['"]\s*([^'"]+)['"]''', self.text):
            if url in processed:
                continue
            links.append(Link(url, ""))
            processed[url] = True

        return links


def create_link_parser(url):
    if "cplusplus.com" in url:
        return CPlusPlusLinkParser()
    elif "cppreference.com" in url:
        return CPPReferenceLinkParser()
    else:
        return None

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

    def process_document(self, doc, std):
        print('GET', doc.status, doc.url, std)
        # to do stuff with url depth use self._calc_depth(doc.url)

    def crawl(self, url, path=None):
        self.root_url = url
        self.link_parser = create_link_parser(url)

        rx = re.match('(https?://)([^/]+)([^\?]*)(\?.*)?', url)
        self.proto = rx.group(1)
        self.host = rx.group(2)
        self.path = rx.group(3)
        self.dir_path = os.path.dirname(self.path)
        self.query = rx.group(4)

        if path:
            self.dir_path = path

        self.targets.add((url, ""))
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

    def _add_target(self, target, std = ""):
        if not target:
            return

        if self.max_depth and self._calc_depth(target) > self.max_depth:
            return

        with self.targets_lock:
          if target in self.visited:
              return
          self.targets.add((target, std))

    def _spawn_new_worker(self):
        with self.concurrency_lock:
          self.concurrency += 1
          t = Thread(target=self._worker, args=(self.concurrency,))
          t.daemon = True
          self.threads.append(t)
          t.start()

    def _worker(self, sid):
        while self.targets:
            try:
                with self.targets_lock:
                  (url, std) = self.targets.pop()
                  self.visited[url] = True

                rx = re.match('(https?)://([^/]+)(.*)', url)
                protocol = rx.group(1)
                host = rx.group(2)
                path = rx.group(3)

                if protocol == 'http':
                    conn = httplib.HTTPConnection(host, timeout=10)
                else:
                    conn = httplib.HTTPSConnection(host, timeout=10)

                conn.request('GET', path)
                res = conn.getresponse()

                if res.status == 404:
                    continue

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
                self.process_document(doc, std)

                # Make unique list
                links = self.link_parser.get_unique_links(doc.text)


                for link in links:
                    rlink = self._follow_link(url, link.url.strip())
                    self._add_target(rlink, link.std)

                if self.concurrency < self.max_outstanding:
                    self._spawn_new_worker()
            except KeyError:
                # Pop from an empty set
                break
            except (httplib.HTTPException, EnvironmentError):
                with self.targets_lock:
                  self.targets.add((url, ""))

        with self.concurrency_lock:
          self.concurrency -= 1
