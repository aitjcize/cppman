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

import re
import sys
from threading import Lock, Thread
from urllib.parse import urljoin, urlparse, urlunparse
import urllib.request

from bs4 import BeautifulSoup

# See https://tools.ietf.org/html/rfc3986#section-3.3
_CONTAINS_DISALLOWED_URL_PCHAR_RE = re.compile('[\x00-\x20\x7f]')

class NoRedirection(urllib.request.HTTPErrorProcessor):
    """A handler that disables redirection"""
    def http_response(self, request, response):
        if response.code in Crawler.F_REDIRECT_CODES:
            return response
        return super().http_response(request, response)

    https_response = http_response

class Crawler(object):
    F_ANY, F_SAME_HOST, F_SAME_PATH = list(range(3))
    F_REDIRECT_CODES = (301, 302)

    def __init__(self):
        self.queued = set()
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

    def link_parser(self, url, content):
        links = re.findall(r'''href\s*=\s*['"]\s*([^'"]+)['"]''', content)
        links = [self._fix_link(url, link) for link in links]
        return links

    def crawl(self, url, path=None):
        self.results = {}
        self.url = urlparse(url)
        if path:
            self.url = self.url._replace(path=path)
        self.url = self.url._replace(fragment="")

        self._add_target(url, 1)
        self._spawn_new_worker()

        while self.threads:
            try:
                for t in self.threads:
                    t.join(1)
                    if not t.is_alive():
                        self.threads.remove(t)
            except KeyboardInterrupt:
                sys.exit(1)
        return self.results

    def _fix_link(self, root, link):
        # Encode invalid characters
        link = re.sub(_CONTAINS_DISALLOWED_URL_PCHAR_RE,
                      lambda m: '%{:02X}'.format(ord(m.group())), link.strip())
        link = urlparse(link)
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

    def _add_target(self, url, depth):
        if not self._valid_link(url):
            return

        if self.max_depth and depth > self.max_depth:
            return

        with self.targets_lock:
            if url in self.queued:
                return
            self.queued.add(url)
            self.targets.add((depth, url))

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
                    if len(self.targets) == 0:
                        continue
                    depth, url = sorted(self.targets)[0]
                    self.targets.remove((depth, url))

                opener = urllib.request.build_opener(NoRedirection)
                res = opener.open(url, timeout=10)

                if res.status in self.F_REDIRECT_CODES:
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

                content = res.read().decode()
                if self.process_document(url, content, depth):

                    # Find links in document
                    links = self.link_parser(url, content)
                    for link in links:
                        self._add_target(link, depth+1)

                if self.concurrency < self.max_outstanding:
                    self._spawn_new_worker()
            except KeyError:
                # Pop from an empty set
                break
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    continue
                self._add_target(url, depth+1)
            except (urllib.error.URLError, EnvironmentError):
                self._add_target(url, depth+1)

        with self.concurrency_lock:
            self.concurrency -= 1
