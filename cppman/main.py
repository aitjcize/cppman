# -*- coding: utf-8 -*-
#
# main.py
#
# Copyright (C) 2010 - 2015  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
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

import gzip
import importlib
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib.request

from cppman import environ
from cppman import util
from cppman.crawler import Crawler


class Cppman(Crawler):
    """Manage cpp man pages, indexes"""
    def __init__(self, forced=False, force_columns=-1):
        Crawler.__init__(self)
        self.results = set()
        self.forced = forced
        self.success_count = None
        self.failure_count = None
        self.force_columns = force_columns

        self.blacklist = [
        ]
        self.name_exceptions = [
            'http://www.cplusplus.com/reference/string/swap/'
        ]

    def extract_name(self, data):
        """Extract man page name from web page."""
        name = re.search('<h1[^>]*>(.+?)</h1>', data).group(1)
        name = re.sub(r'<([^>]+)>', r'', name)
        name = re.sub(r'&gt;', r'>', name)
        name = re.sub(r'&lt;', r'<', name)
        return name

    def rebuild_index(self):
        """Rebuild index database from cplusplus.com and cppreference.com."""
        try:
            os.remove(environ.index_db_re)
        except:
            pass

        self.db_conn = sqlite3.connect(environ.index_db_re)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute('CREATE TABLE "cplusplus.com" '
                               '(name VARCHAR(255), url VARCHAR(255), std VARCHAR(255))')
        self.db_cursor.execute('CREATE TABLE "cppreference.com" '
                               '(name VARCHAR(255), url VARCHAR(255), std VARCHAR(255))')

        try:
            self.add_url_filter('\.(jpg|jpeg|gif|png|js|css|swf|svg)$')
            self.set_follow_mode(Crawler.F_SAME_PATH)

            # cplusplus.com
            self.crawl('http://www.cplusplus.com/reference/')
            for name, url, std in self.results:
                self.insert_index('cplusplus.com', name, url, std)
            self.db_conn.commit()

            # Rename duplicate entries
            duplicates = self.db_cursor.execute('SELECT name, COUNT(name) '
                                                'AS NON '
                                                'FROM "cplusplus.com" '
                                                'GROUP BY NAME '
                                                'HAVING (NON > 1)').fetchall()
            for name, num in duplicates:
                dump = self.db_cursor.execute('SELECT name, url FROM '
                                              '"cplusplus.com" WHERE name="%s"'
                                              % name).fetchall()
                for n, u in dump:
                    if u not in self.name_exceptions:
                        n2 = n[5:] if n.startswith('std::') else n
                        try:
                            group = re.search('/([^/]+)/%s/$' % n2, u).group(1)
                        except Exception:
                            group = re.search('/([^/]+)/[^/]+/$', u).group(1)

                        new_name = '%s (%s)' % (n, group)
                        self.db_cursor.execute('UPDATE "cplusplus.com" '
                                               'SET name="%s", url="%s" '
                                               'WHERE url="%s"' %
                                               (new_name, u, u))
            self.db_conn.commit()

            # cppreference.com
            self.results = set()
            self.crawl('https://en.cppreference.com/w/cpp', '/w/cpp')

            for name, url, std in self.results:
                self.insert_index('cppreference.com', name, url, std)
            self.db_conn.commit()

        except KeyboardInterrupt:
            os.remove(environ.index_db_re)
            raise KeyboardInterrupt
        finally:
            self.db_conn.close()

    def process_document(self, doc, std):
        """callback to insert index"""
        if doc.url not in self.blacklist:
            print("Indexing '%s' %s..." % (doc.url, std))
            name = self.extract_name(doc.text)
            self.results.add((name, doc.url, std))
        else:
            print("Skipping blacklisted page '%s' ..." % doc.url)
            return None

    def insert_index(self, table, name, url, std=""):
        """callback to insert index"""
        names = name.split(',')

        if len(names) > 1:
            m = re.match(r'^\s*(.*?::(?:operator)?)([^:]*)\s*$', names[0])
            if m:
                prefix = m.group(1)
                names[0] = m.group(2)
                names = [prefix + n for n in names]

        for n in names:
            self.db_cursor.execute(
                'INSERT INTO "%s" (name, url, std) VALUES ("%s", "%s", "%s")' %
                (table, n.strip(), url, std))

    def cache_all(self):
        """Cache all available man pages"""

        respond = input(
              'By default, cppman fetches pages on-the-fly if corresponding '
              'page is not found in the cache. The "cache-all" option is only '
              'useful if you want to view man pages offline. '
              'Caching all contents will take several minutes, '
              'do you want to continue [y/N]? ')
        if not (respond and 'yes'.startswith(respond.lower())):
            raise KeyboardInterrupt

        try:
            os.makedirs(environ.cache_dir)
        except:
            pass

        self.success_count = 0
        self.failure_count = 0

        if not os.path.exists(environ.index_db):
            raise RuntimeError("can't find index.db")

        conn = sqlite3.connect(environ.index_db)
        cursor = conn.cursor()

        source = environ.config.source
        print('Caching manpages from %s ...' % source)
        data = cursor.execute('SELECT * FROM "%s"' % source).fetchall()

        for name, url, _ in data:
            print('Caching %s ...' % name)
            retries = 3
            while retries > 0:
                try:
                    self.cache_man_page(source, url, name)
                except Exception:
                    print('Retrying ...')
                    retries -= 1
                else:
                    self.success_count += 1
                    break
            else:
                print('Error caching %s ...' % name)
                self.failure_count += 1

        conn.close()

        print('\n%d manual pages cached successfully.' % self.success_count)
        print('%d manual pages failed to cache.' % self.failure_count)
        self.update_mandb(False)

    def cache_man_page(self, source, url, name):
        """callback to cache new man page"""
        # Skip if already exists, override if forced flag is true
        outname = self.get_page_path(source, name)
        if os.path.exists(outname) and not self.forced:
            return

        try:
            os.makedirs(os.path.join(environ.cache_dir, source))
        except OSError:
            pass

        # There are often some errors in the HTML, for example: missing closing
        # tag. We use fixupHTML to fix this.
        data = util.fixupHTML(urllib.request.urlopen(url).read())

        formatter = importlib.import_module('cppman.formatter.%s' % source[:-4])
        groff_text = formatter.html2groff(data, name)

        with gzip.open(outname, 'w') as f:
            f.write(groff_text.encode('utf-8'))

    def clear_cache(self):
        """Clear all cache in man"""
        shutil.rmtree(environ.cache_dir)

    def man(self, pattern):
        """Call viewer.sh to view man page"""
        try:
            avail = os.listdir(os.path.join(environ.cache_dir, environ.source))
        except OSError:
            avail = []

        if not os.path.exists(environ.index_db):
            raise RuntimeError("can't find index.db")

        conn = sqlite3.connect(environ.index_db)
        cursor = conn.cursor()

        # Try direct match
        try:
            page_name, url = cursor.execute(
                'SELECT name,url FROM "%s" '
                'WHERE name="%s" ORDER BY LENGTH(name)'
                % (environ.source, pattern)).fetchone()
        except TypeError:
            # Try standard library
            try:
                page_name, url = cursor.execute(
                    'SELECT name,url FROM "%s" '
                    'WHERE name="std::%s" ORDER BY LENGTH(name)'
                    % (environ.source, pattern)).fetchone()
            except TypeError:
                try:
                    page_name, url = cursor.execute(
                        'SELECT name,url FROM "%s" '
                        'WHERE name LIKE "%%%s%%" ORDER BY LENGTH(name)'
                        % (environ.source, pattern)).fetchone()
                except TypeError:
                    raise RuntimeError('No manual entry for ' + pattern)
        finally:
            conn.close()

        page_filename = self.get_normalized_page_name(page_name)
        if self.forced or page_filename + '.3.gz' not in avail:
            self.cache_man_page(environ.source, url, page_name)

        pager_type = environ.pager if sys.stdout.isatty() else 'pipe'

        # Call viewer
        columns = (util.get_width() if self.force_columns == -1 else
                   self.force_columns)
        pid = os.fork()
        if pid == 0:
            os.execl('/bin/sh', '/bin/sh', environ.pager_script, pager_type,
                     self.get_page_path(environ.source, page_name),
                     str(columns), environ.pager_config, page_name)
        return pid

    def find(self, pattern):
        """Find pages in database."""

        if not os.path.exists(environ.index_db):
            raise RuntimeError("can't find index.db")

        conn = sqlite3.connect(environ.index_db)
        cursor = conn.cursor()
        selected = cursor.execute(
            'SELECT * FROM "%s" WHERE name '
            'LIKE "%%%s%%" ORDER BY LENGTH(name)'
            % (environ.source, pattern)).fetchall()

        pat = re.compile('(%s)' % pattern, re.I)

        if selected:
            for name, url, std in selected:
                if os.isatty(sys.stdout.fileno()):
                    print(pat.sub(r'\033[1;31m\1\033[0m', name) +
                          (' \033[1;33m[%s]\033[0m' % std if std else ''))
                else:
                    print(name + (' [%s]' % std if std else ''))
        else:
            raise RuntimeError('%s: nothing appropriate.' % pattern)

    def update_mandb(self, quiet=True):
        """Update mandb."""
        if not environ.config.UpdateManPath:
            return
        print('\nrunning mandb...')
        cmd = 'mandb %s' % (' -q' if quiet else '')
        subprocess.Popen(cmd, shell=True).wait()

    def get_normalized_page_name(self, name):
        return name.replace('/', '_')

    def get_page_path(self, source, name):
        name = self.get_normalized_page_name(name)
        return os.path.join(environ.cache_dir, source, name + '.3.gz')
