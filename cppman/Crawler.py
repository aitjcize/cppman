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

import re

from threading import Thread, Lock
from time import sleep
from urllib import urlopen, unquote

class Crawler(object):
    '''
    A Crawler that crawls through cplusplus.com
    '''
    def __init__(self):
        self.origin = '/reference/'
        self.url_base = 'http://www.cplusplus.com'
        self.visited = []
        self.targets = set()
        self.processes = []
        self.concurrency = 0
        self.results = set()

        self.targets_lock = Lock()
        self.visited_lock = Lock()
        self.concurrency_lock = Lock()

    def crawl(self, extract, insert):
        self.targets.add(self.origin)
        self.extract = extract

        self.concurrency_lock.acquire()
        self.spawn_new_worker()
        self.concurrency_lock.release()

        while self.processes:
            p = self.processes.pop()
            p.join()

        for name, url in self.results:
            insert(name, url)

    def spawn_new_worker(self):
        self.concurrency += 1
        p = Thread(target=self.worker, args=(self.concurrency,))
        self.processes.append(p)
        p.start()

    def worker(self, sid):
        self.concurrency_lock.acquire()
        print 'Thread started: %d' % sid
        self.concurrency_lock.release()

        while self.targets:
            try:
                self.targets_lock.acquire()
                url = self.targets.pop()
                self.targets_lock.release()
                real_url = unquote(urlopen(self.url_base + url).geturl())

                if not real_url.startswith(self.url_base + self.origin):
                    continue

                self.visited_lock.acquire()
                if real_url in self.visited:
                    self.visited_lock.release()
                    continue
                self.visited_lock.release()

                data = urlopen(real_url).read()
                result = self.extract(real_url, data)
                if result:
                    self.results.add(result)

                self.visited_lock.acquire()
                self.visited.append(url)
                self.visited.append(real_url)
                self.visited_lock.release()

                # Remove sidebar
                try:
                    data = data[data.index('<div class="doctop"><h1>'):]
                except ValueError: pass

                # Make unique list
                links = re.findall('<a\s+href\s*=\s*"(/.*?)"', data, re.S)
                links = list(set(links))

                self.visited_lock.acquire()
                self.targets_lock.acquire()
                for link in links:
                    if not link in self.visited:
                        self.targets.add(link)
                self.targets_lock.release()
                self.visited_lock.release()

                self.concurrency_lock.acquire()
                if self.concurrency < 16:
                    self.spawn_new_worker()
                self.concurrency_lock.release()
            except IndexError as e:
                print e
                break
            except Exception as e:
                print '%s, retrying' % str(e)
                self.targets_lock.acquire()
                self.targets.add(url)
                self.targets_lock.release()
            else:
                continue

        self.concurrency_lock.acquire()
        self.concurrency -= 1
        self.concurrency_lock.release()
