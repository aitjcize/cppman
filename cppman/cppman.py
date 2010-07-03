#-*- coding: utf-8 -*-
# 
# cppman.py 
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
import os
import os.path
import re
import shutil
import sqlite3
import subprocess
import urllib

import environ
import formatter
from crawler import Crawler

class cppman(Crawler):
    '''
    Mange cpp man pages, indexes
    '''
    def __init__(self):
        Crawler.__init__(self)
        self.forced = False

    def extract_name(self, data):
        '''
        Extract man page name from cplusplus web page.
        '''
        name = re.search('<h1>(.+?)</h1>', data).group(1)
        name = re.sub(r'<([^>]+)>', r'', name)
        return name

    def rebuild_index(self):
        try:
            os.remove(environ.index_db)
        except: pass
        self.db_conn = sqlite3.connect(environ.index_db)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute('CREATE TABLE CPPMAN (name varchar(255), '
                               'url varchar(255))')
        self.crawl(self.insert_index)
        self.db_conn.commit()
        self.db_conn.close()

    def insert_index(self, url):
        '''
        callback to insert index
        '''
        name = self.extract_name(urllib.urlopen(url).read())
        self.db_cursor.execute('INSERT INTO CPPMAN (name, url) VALUES '
                               '("%s", "%s")' % (name, url))

    def cache_all(self, forced = False):
        '''
        Cache all available man pages from cplusplus.com to 
        '''
        self.forced = forced

        print 'By defualt, cppman fetch pages on the fly if coressponding '\
            'page is not found in the cache. The "cache-all" option is only '\
            'useful if you want to view man pages offline.'
        print 'Caching all contents from cplusplus.com could take a LONG '\
            'time, do you want to continue [Y/n]? ',

        respond = raw_input()
        if respond.lower() not in ['y', 'ye', 'yes']:
            print 'Aborted.'
            return

        try:
            os.mkdir(environ.man_dir)
        except: pass
        self.crawl(self.cache_man_page)

    def cache_man_page(self, url):
        '''
        callback to cache new man page
        '''
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

    def clear_cache(self):
        '''
        Clear all cache in man3
        '''
        shutil.rmtree(environ.man_dir)

    def man(self, pattern):
        '''
        Call viewer.sh to view man page
        '''
        try:
            os.mkdir(environ.man_dir)
        except: pass

        avail = subprocess.Popen('ls %s' % environ.man_dir, shell=True,
                                 stdout=subprocess.PIPE).stdout.read()
        conn = sqlite3.connect(environ.index_db)
        cursor = conn.cursor()
        try:
            page_name, url = cursor.execute('SELECT name,url FROM CPPMAN WHERE'
                                ' name LIKE "%%%s%%"' % pattern).fetchone()
        except TypeError:
            raise RuntimeError('No manual entry for ' + pattern)
        finally:
            conn.close()

        if page_name + '.3.gz' not in avail:
            self.cache_man_page(url)

        os.execl(environ.viewer, 'dummy', str(formatter.get_width()),
                 environ.man_dir + page_name + '.3.gz')

    def find(self, pattern):
        pass
