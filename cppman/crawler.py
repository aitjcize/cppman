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

    from urllib import quote, urlparse, urlunparse, urljoin
else:
    import http.client as httplib
    from urllib.parse import quote, urlparse, urlunparse, urljoin


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
    F_ANY, F_SAME_HOST, F_SAME_PATH = list(range(3))

    def __init__(self):
        self.queued  = set()
        self.targets = set()
        self.threads = []
        self.concurrency = 0
        self.max_outstanding = 16
        self.max_depth = 0
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
        if mode > 2:
            raise RuntimeError('invalid follow mode %s.' % mode)
        self.follow_mode = mode

    def set_concurrency_level(self, level):
        self.max_outstanding = level

    def set_max_depth(self, max_depth):
        self.max_depth = max_depth

    def crawl(self, url, path=None):
        self.link_parser = create_link_parser(url)

        self.url = urlparse(url)
        if path:
            self.url = self.url._replace(path=path)
        self.url = self.url._replace(fragment="")

        self._add_target(url, 1, "")
        self._spawn_new_worker()

        while self.threads:
            try:
                for t in self.threads:
                    t.join(1)
                    if not t.isAlive():
                        self.threads.remove(t)
            except KeyboardInterrupt:
                sys.exit(1)

    def _fix_link(self, root, link):
        link =  urlparse(link.strip())
        if (link.fragment != ""):
            link = link._replace(fragment="")
        return urljoin(root, urlunparse(link))

    def _valid_link(self, link):
        if not link:
            return False

        link = urlparse(link)
        if self.follow_mode == self.F_ANY:
            return True
        elif self.follow_mode == self.F_SAME_HOST:
            return self.url.hostname == link.hostname
        elif self.follow_mode == self.F_SAME_PATH:
            return self.url.hostname == link.hostname and \
                link.path.startswith(self.url.path)
        return False

    def _add_target(self, url, depth, std = ""):
        if not self._valid_link(url):
            return

        if self.max_depth and depth > self.max_depth:
            return

        with self.targets_lock:
          if url in self.queued:
              return
          self.queued.add(url)
          self.targets.add((depth, url, std))

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
                  (depth, url, std) = sorted(self.targets)[0]
                  self.targets.remove((depth, url, std))

                url_p = urlparse(url)

                if url_p.scheme == "http":
                    conn = httplib.HTTPConnection(url_p.netloc, timeout=10)
                elif url_p.scheme == "https":
                    conn = httplib.HTTPSConnection(url_p.netloc, timeout=10)
                else:
                    raise RuntimeError('Unknown protocol %s' % url_p.scheme)

                conn.request('GET', url_p.path)
                res = conn.getresponse()

                if res.status == 404:
                    continue

                if res.status == 301 or res.status == 302:
                    target = self._fix_link(url, res.getheader('location'))
                    self._add_target(target, depth+1)
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
                self.process_document(doc, depth, std)

                # Make unique list
                links = self.link_parser.get_unique_links(doc.text)


                for link in links:
                    link.url = self._fix_link(url, link.url)
                    self._add_target(link.url, depth+1, link.std)

                if self.concurrency < self.max_outstanding:
                    self._spawn_new_worker()
            except KeyError:
                # Pop from an empty set
                break
            except (httplib.HTTPException, EnvironmentError):
                with self.targets_lock:
                  self._add_target(url, depth+1, "")

        with self.concurrency_lock:
          self.concurrency -= 1
