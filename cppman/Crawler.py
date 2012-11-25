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

import urllib.request, urllib.parse, urllib.error
import re

class Crawler(object):
    '''
    A Crawler that crawls through cplusplus.com
    '''
    def __init__(self):
        self.origin = 'http://www.cplusplus.com/reference/'
        self.url_base = 'http://www.cplusplus.com'
        self.visited = []

    def crawl(self, callback):
        self.crawl_page(self.origin, callback)

    def crawl_page(self, url, callback):
        '''
        Crawl a new page.
        '''
        data = urllib.request.urlopen(url).read()

        # Remove sidebar
        try:
            data = data[data.index('<div class="doctop"><h1>'):]
        except ValueError: pass

        # Make unique list
        links = re.findall('<a\s+href\s*=\s*"(/.*?)"', data, re.DOTALL)
        links = list(set(links))

        for link in links:
            real_url = urllib.request.urlopen(self.url_base + link).geturl()
            real_url = urllib.parse.unquote(real_url)

            if real_url in self.visited or not real_url.startswith(
                'http://www.cplusplus.com/reference/'):
                continue

            self.visited.append(real_url)

            # Run callback
            callback(real_url)

            self.crawl_page(self.url_base + link, callback)
