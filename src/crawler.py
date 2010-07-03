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

import gzip
import os.path
import sqlite3
import sys
import urllib
import re

import environ
import formatter

class Crawler:
    point_of_origin = 'http://www.cplusplus.com/reference/'
    url_base = 'http://www.cplusplus.com'
    visited = []

    def __init__(self, forced):
        self.forced = forced

    def crawl(self, callback):
        self.crawl_page(self.point_of_origin, callback)

    def crawl_page(self, url, callback):
        '''
        Crawl a new page.
        '''
        data = urllib.urlopen(url).read()

        # Remove sidebar
        try:
            data = data[data.index('<div class="doctop"><h1>'):]
        except ValueError: pass

        # Make unique list
        links = re.findall('<a href="(/.*?)"', data, re.DOTALL)
        links = list(set(links))

        for link in links:
            real_url = urllib.urlopen(self.url_base + link).geturl()
            if real_url in self.visited or not real_url.startswith(
                'http://www.cplusplus.com/reference/'):
                continue

            print real_url
            self.visited.append(real_url)

            # Run callback
            callback(real_url)

            self.crawl_page(self.url_base + link, callback)

    def extract_name(self, data):
        '''
        Extract man page name from cplusplus web page.
        '''
        name = re.search('<h1>(.+?)</h1>', data).group(1)
        name = re.sub(r'<([^>]+)>', r'', name)
        return name

    def build_index(self):
        try:
            os.remove(environ.index_db)
        except: pass
        self.db_conn = sqlite3.connect(environ.index_db)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute('CREATE TABLE CPPMAN (name varchar(255), '
                               'url varchar(255))')
        self.crawl(self.insert_index)
        self.db_conn.commit()

    def insert_index(self, url):
        name = self.extract_name(urllib.urlopen(url).read())
        self.db_cursor.execute('INSERT INTO CPPMAN (name, url) VALUES '
                               '("%s", "%s")' % (name, url))

    def cache_all(self):
        self.crawl(self.cache_man_page)

    def cache_man_page(self, url):
        data = urllib.urlopen(url).read()
        groff_text = formatter.cplusplus2groff(data)
        name = self.extract_name(data)

        # Skip if already exists, override if forced flag is true
        outname = environ.man_dir + name + '.3.gz'
        if os.path.exists(outname) and not self.forced:
            return
        f = gzip.open(outname, 'w')
        f.write(groff_text)
        f.close()

if __name__ == '__main__':
    cw = Crawler(False)
    cw.build_index()
