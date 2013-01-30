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
from urllib import urlopen, unquote
from time import sleep

class Crawler(object):
    '''
    A Crawler that crawls through cplusplus.com
    '''
    def __init__(self):
        self.origin = '/reference/'
        self.url_base = 'http://www.cplusplus.com'
        self.visited = []

    def crawl(self, callback):
        self.crawl_page(self.origin, callback)

    def crawl_page(self, base_url, callback):
        '''
        Crawl a new page.
        '''
        self.visited = []
        self.targets = [base_url]


        while self.targets:
            while True:
                try:
                    url = self.targets.pop()
                    real_url = unquote(urlopen(self.url_base + url).geturl())

                    if real_url in self.visited:
                        break

                    if not real_url.startswith(self.url_base + self.origin):
                        break

                    data = urlopen(real_url).read()
                    callback(real_url, data)

                    self.visited.append(url)
                    self.visited.append(real_url)

                    # Remove sidebar
                    try:
                        data = data[data.index('<div class="doctop"><h1>'):]
                    except ValueError: pass

                    # Make unique list
                    links = re.findall('<a\s+href\s*=\s*"(/.*?)"', data, re.S)
                    links = list(set(links))

                    for link in links:
                        if not (link in self.visited or link in self.targets):
                            self.targets.append(link)
                except Exception as e:
                    print '%s, retrying' % str(e)
                    self.targets.append(url)
                else:
                    break
