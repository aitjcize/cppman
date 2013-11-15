#-*- coding: utf-8 -*-
# 
# cppman.py 
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

import gzip
import os
import os.path
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib

import Environ
import Formatter
from Crawler import Crawler

class cppman(Crawler):
    """Manage cpp man pages, indexes"""
    def __init__(self, forced=False):
        Crawler.__init__(self)
        self.results = set()
        self.forced = forced
        self.success_count = None
        self.failure_count = None

        self.blacklist = [
        ]
        self.name_exceptions = [
            'http://www.cplusplus.com/reference/string/swap/'
        ]

    def extract_name(self, data):
        """Extract man page name from cplusplus web page."""
        name = re.search('<h1>(.+?)</h1>', data).group(1)
        name = re.sub(r'<([^>]+)>', r'', name)
        name = re.sub(r'&gt;', r'>', name)
        name = re.sub(r'&lt;', r'<', name)
        return name

    def rebuild_index(self):
        """Rebuild index database from cplusplus.com."""
        try:
            os.remove(Environ.index_db_re)
        except: pass
        self.db_conn = sqlite3.connect(Environ.index_db_re)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute('CREATE TABLE CPPMAN (name VARCHAR(255), '
                               'url VARCHAR(255))')
        try:
            self.add_url_filter('\.(jpg|jpeg|gif|png|js|css|swf)$')
            self.set_follow_mode(Crawler.F_SAME_PATH)
            self.crawl('http://www.cplusplus.com/reference/')
            for name, url in self.results:
                self.insert_index(name, url)
            self.db_conn.commit()

            # Rename dumplicate entries
            dumplicates = self.db_cursor.execute('SELECT name, COUNT(name) '
                                                 'AS NON '
                                                 'FROM CPPMAN '
                                                 'GROUP BY NAME '
                                                 'HAVING (NON > 1)').fetchall()
            for name, num in dumplicates:
                dump = self.db_cursor.execute('SELECT name, url FROM CPPMAN '
                                              'WHERE name="%s"'
                                              % name).fetchall()
                for n, u in dump:
                    if u not in self.name_exceptions:
                        n2 = n[5:] if n.startswith('std::') else n
                        try:
                            group = re.search('/([^/]+)/%s/$' % n2, u).group(1)
                        except Exception:
                            group = re.search('/([^/]+)/[^/]+/$', u).group(1)

                        new_name = '%s (%s)' % (n, group)
                        self.db_cursor.execute('UPDATE CPPMAN '
                                               'SET name="%s", url="%s" '
                                               'WHERE url="%s"' %
                                               (new_name, u, u))
            self.db_conn.commit()
        except KeyboardInterrupt:
            os.remove(Environ.index_db_re)
            raise KeyboardInterrupt
        finally:
            self.db_conn.close()

    def process_document(self, doc):
        """callback to insert index"""
        if doc.url not in self.blacklist:
            print "Indexing '%s' ..." % doc.url
            name = self.extract_name(doc.text)
            self.results.add((name, doc.url))
        else:
            print "Skipping blacklisted page '%s' ..." % doc.url
            return None

    def insert_index(self, name, url):
        """callback to insert index"""
        self.db_cursor.execute('INSERT INTO CPPMAN (name, url) VALUES '
                               '("%s", "%s")' % (name, url))

    def cache_all(self):
        """Cache all available man pages from cplusplus.com"""
        print 'By defualt, cppman fetch pages on the fly if coressponding '\
            'page is not found in the cache. The "cache-all" option is only '\
            'useful if you want to view man pages offline. ' \
            'Caching all contents from cplusplus.com will serveral'\
            'minutes, do you want to continue [Y/n]?',

        respond = raw_input()
        if respond.lower() not in ['y', 'ye', 'yes']:
            raise KeyboardInterrupt

        try:
            os.makedirs(Environ.man_dir)
        except: pass

        self.success_count = 0
        self.failure_count = 0

        if not os.path.exists(Environ.index_db):
            raise RuntimeError("can't find index.db")

        conn = sqlite3.connect(Environ.index_db)
        cursor = conn.cursor()

        data = cursor.execute('SELECT name, url FROM CPPMAN').fetchall()

        for name, url in data:
            try:
                print 'Caching %s ...' % name
                self.cache_man_page(url, name)
            except Exception, e:
                print 'Error caching %s ...', name
                self.failure_count += 1
            else:
                self.success_count += 1
        conn.close()

        print '\n%d manual pages cached successfully.' % self.success_count
        print '%d manual pages failed to cache.' % self.failure_count
        self.update_mandb(False)

    def cache_man_page(self, url, name=None):
        """callback to cache new man page"""
        data = urllib.urlopen(url).read()
        groff_text = Formatter.cplusplus2groff(data)
        if not name:
            name = self.extract_name(data).replace('/', '_')

        # Skip if already exists, override if forced flag is true
        outname = Environ.man_dir + name + '.3.gz'
        if os.path.exists(outname) and not self.forced:
            return
        f = gzip.open(outname, 'w')
        f.write(groff_text)
        f.close()

    def clear_cache(self):
        """Clear all cache in man3"""
        shutil.rmtree(Environ.man_dir)

    def man(self, pattern):
        """Call viewer.sh to view man page"""
        try:
            os.makedirs(Environ.man_dir)
        except: pass

        avail = os.listdir(Environ.man_dir)

        if not os.path.exists(Environ.index_db):
            raise RuntimeError("can't find index.db")

        conn = sqlite3.connect(Environ.index_db)
        cursor = conn.cursor()

        # Try direct match
        try:
            page_name, url = cursor.execute('SELECT name,url FROM CPPMAN WHERE'
                    ' name="%s" ORDER BY LENGTH(name)' % pattern).fetchone()
        except TypeError:
            # Try standard library
            try:
                page_name, url = cursor.execute('SELECT name,url FROM CPPMAN'
                        ' WHERE name="std::%s" ORDER BY LENGTH(name)'
                        % pattern).fetchone()
            except TypeError:
                try:
                    page_name, url = cursor.execute('SELECT name,url FROM '
                        'CPPMAN WHERE name LIKE "%%%s%%" ORDER BY LENGTH(name)'
                        % pattern).fetchone()
                except TypeError:
                    raise RuntimeError('No manual entry for ' + pattern)
        finally:
            conn.close()

        page_name = page_name.replace('/', '_')
        if page_name + '.3.gz' not in avail or self.forced:
            self.cache_man_page(url, page_name)
            self.update_mandb()

        pager = Environ.pager if sys.stdout.isatty() else Environ.renderer

        # Call viewer
        pid = os.fork()
        if pid == 0:
            os.execl('/bin/sh', '/bin/sh', pager,
                     Environ.man_dir + page_name + '.3.gz',
                     str(Formatter.get_width()), Environ.pager_config,
                     page_name)
        return pid

    def find(self, pattern):
        """Find pages in database."""

        if not os.path.exists(Environ.index_db):
            raise RuntimeError("can't find index.db")

        conn = sqlite3.connect(Environ.index_db)
        cursor = conn.cursor()
        selected = cursor.execute('SELECT name,url FROM CPPMAN WHERE name '
                'LIKE "%%%s%%" ORDER BY LENGTH(name)' % pattern).fetchall()

        pat = re.compile('(%s)' % pattern, re.I)

        if selected:
            for name, url in selected:
                if os.isatty(sys.stdout.fileno()):
                    print pat.sub(r'\033[1;31m\1\033[0m', name)
                else:
                    print name
        else:
            raise RuntimeError('%s: nothing appropriate.' % pattern)

    def update_mandb(self, quiet=True):
        """Update mandb."""
        if not Environ.config.UpdateManPath:
            return
        print '\nrunning mandb...'
        cmd = 'mandb %s' % (' -q' if quiet else '')
        handle = subprocess.Popen(cmd, shell=True).wait()
