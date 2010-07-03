#!/usr/bin/env python
#-*- coding: utf-8 -*-
# 
# crawler.py
#
# Copyright (C) 2010 -  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
# All Rights reserved.
#
# This file is part of manpages-cpp.
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

import formatter
import os.path
import sys
import urllib
import re

class Crawler:
    point_of_origin = 'http://www.cplusplus.com/reference/'
    url_base = 'http://www.cplusplus.com'
    man_base = 'man3/'
    visited = []

    def __init__(self, forced):
        self.forced = forced

    def crawl(self):
        self.crawl_page(self.point_of_origin, 0)

    def crawl_page(self, url, depth):
        '''
        Crawl a new page.
        '''
        print '----------- In depth ', depth

        data = urllib.urlopen(url).read()

        # Remove sidebar
        try:
            data = data[data.index('<div class="doctop"><h1>'):]
        except ValueError: pass

        # Make unique list
        links = re.findall('<a href="(/.*?)"', data, re.DOTALL)
        links = list(set(links))

        for link in links:
            urlobj = urllib.urlopen(self.url_base + link)
            real_url = urlobj.geturl()
            if real_url in self.visited or not real_url.startswith(
                'http://www.cplusplus.com/reference/'):
                continue
            print real_url

            self.visited.append(real_url)
            name, groff_text = formatter.cplusplus2groff(urlobj.read())

            # Skip if already exists, override if forced flag is true
            if os.path.exists(self.man_base + name) and not self.forced:
                continue

            with open(self.man_base + name, 'w') as f:
                f.write(groff_text)

        for link in links:
            self.crawl_page(self.url_base + link, depth + 1)

cw = Crawler(False)
cw.crawl()
