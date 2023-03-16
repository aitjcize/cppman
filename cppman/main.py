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

import collections
import gzip
import html
import importlib
import os
import os.path
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib.request

from bs4 import BeautifulSoup
from cppman import environ, util
from cppman.crawler import Crawler
from urllib.parse import urlparse, unquote



def _sort_crawl(entry):
    """ Sorting entries for putting '(1)' indexes behind keyword

        1. keywords that have 'std::' in them have highest priority
        2. priority if 'std::' is inside their name
        3. sorting by keyword
        4. sorting by name
    """
    id, title, keyword, count = entry
    hasStd1 = keyword.find("std::")
    if hasStd1 == -1:
        hasStd1 = 1
    else:
        hasStd1 = 0

    hasStd2 = title.find("std::")
    if hasStd2 == -1:
        hasStd2 = 1
    else:
        hasStd2 = 0

    return (hasStd1, hasStd2, keyword, title)


def _sort_search(entry, pattern):
    """ Sort results
        1. sort by 'std::' (an entry with `std::` goes before an entry without)
        2. sort by which position the keyword appears
    """

    title, keyword, url = entry
    hasStd1 = keyword.find("std::")
    if hasStd1 == -1:
        hasStd1 = 1
    else:
        hasStd1 = 0

    hasStd2 = title.find("std::")
    if hasStd2 == -1:
        hasStd2 = 1
    else:
        hasStd2 = 0

    return (hasStd1, hasStd2, keyword.find(pattern), keyword)

# Return the longest prefix of all list elements.
def _commonprefix(s1, s2):
    """" Given two strings, returns the longest common leading prefix """

    if len(s1) > len(s2):
        s1, s2 = s2, s1;
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1

def _removeprefix(string, prefix):
    if prefix and string.startswith(prefix):
        return string[len(prefix):]
    return string

def _removesuffix(string, suffix):
    if suffix and string.endswith(suffix):
        return string[:-len(suffix)]
    return string

class Cppman(Crawler):
    """ Manage cpp man pages, indexes. """

    def __init__(self, forced=False, force_columns=-1):
        Crawler.__init__(self)
        self.forced = forced
        self.success_count = None
        self.failure_count = None
        self.force_columns = force_columns

    def rebuild_index(self):
        """ Rebuild index database from cplusplus.com and cppreference.com. """

        self.db_conn = sqlite3.connect(environ.index_db_re)
        self.db_cursor = self.db_conn.cursor()
        try:
            self.add_url_filter('\.(jpg|jpeg|gif|png|js|css|swf|svg)$')
            self.set_follow_mode(Crawler.F_SAME_PATH)

            sources = [('cplusplus.com', 'https://cplusplus.com/reference/', None),
                       ('cppreference.com', 'https://en.cppreference.com/w/cpp', '/w/cpp')]

            for table, url, path in sources:
                """ Drop and recreate tables. """
                self.db_cursor.execute(
                    'DROP TABLE IF EXISTS "%s"'
                    % table)

                self.db_cursor.execute(
                    'DROP TABLE IF EXISTS "%s_keywords"'
                    % table)

                self.db_cursor.execute(
                    'CREATE TABLE "%s" ('
                    'id INTEGER NOT NULL PRIMARY KEY, '
                    'title VARCHAR(255) NOT NULL UNIQUE, '
                    'url VARCHAR(255) NOT NULL UNIQUE'
                    ')' % table)

                self.db_cursor.execute(
                    'CREATE TABLE "%s_keywords" ('
                    'id INTEGER NOT NULL, '
                    'keyword VARCHAR(255), '
                    'FOREIGN KEY(id) REFERENCES "%s"(id)'
                    ')' % (table, table))

                """ Crawl and insert all entries. """
                self.results = collections.defaultdict(list)
                self.crawl(url)
                results = self._results_with_unique_title()

                for title in results:
                    """ 1. insert title """
                    self.db_cursor.execute(
                        'INSERT INTO "%s" (title, url) VALUES (?, ?)'
                        % table, (title, results[title]["url"]))

                    lastRow = self.db_cursor.execute(
                        'SELECT last_insert_rowid()').fetchall()[0][0]

                    """ 2. insert all keywords """
                    for k in results[title]["keywords"]:
                        self.db_cursor.execute(
                            'INSERT INTO "%s_keywords" (id, keyword) '
                            'VALUES (?, ?)'
                            % table, (lastRow, k))

                """ 3. add all aliases """
                for title in results:
                    for (k, a) in results[title]["aliases"]:
                        """ search for combinations of words

                            e.g. std::basic_string::append
                        """
                        sql_results = self.db_cursor.execute(
                            'SELECT id, keyword FROM "%s_keywords" '
                            'WHERE keyword LIKE "%%::%s::%%" '
                            'OR keyword LIKE "%s::%%" '
                            'OR keyword LIKE "%s" '
                            'OR keyword LIKE "%s %%" '
                            'OR keyword LIKE "%s)%%" '
                            'OR keyword LIKE "%s,%%"'
                            % (table, k, k, k, k, k, k)).fetchall()

                        for id, keyword in sql_results:
                            keyword = keyword.replace("%s" % k, "%s" % a)

                            self.db_cursor.execute(
                                'INSERT INTO "%s_keywords" (id, keyword) '
                                'VALUES (?, ?)'
                                % table, (id, keyword))

                self.db_conn.commit()

                """ remove duplicate keywords that link the same page """
                self.db_cursor.execute(
                    'DELETE FROM "%s_keywords" WHERE rowid NOT IN ('
                    'SELECT min(rowid) FROM "%s_keywords" '
                    'GROUP BY id, keyword '
                    ')' % (table, table)).fetchall()

                """ give duplicate keywords with different links entry numbers """
                results = self.db_cursor.execute(
                    'SELECT t3.id, t3.title, t2.keyword, t1.count '
                    'FROM ('
                    '      SELECT keyword, COUNT(*) AS count FROM "%s_keywords" '
                    '      GROUP BY keyword HAVING count > 1) AS t1 '
                    'JOIN "%s_keywords" AS t2 '
                    'JOIN "%s" AS t3 '
                    'WHERE t1.keyword = t2.keyword AND t3.id = t2.id '
                    'ORDER BY t2.keyword, t3.title'
                    % (table, table, table)).fetchall()

                keywords = {}
                results = sorted(results, key=_sort_crawl)
                for id, title, keyword, count in results:
                    if not keyword in keywords:
                        keywords[keyword] = 0
                    keywords[keyword] += 1
                    new_keyword = "%s (%s)" % (keyword, keywords[keyword])
                    self.db_cursor.execute(
                        'UPDATE "%s_keywords" SET keyword=? WHERE '
                        'id=? AND keyword=?'
                        % table, (new_keyword, id, keyword))

                self.db_conn.commit()

        except KeyboardInterrupt:
            os.remove(environ.index_db_re)
            raise KeyboardInterrupt
        finally:
            self.db_conn.close()

    def process_document(self, url, content, depth):
        """callback to insert index"""
        print("Indexing '%s' (depth %s)..." % (url, depth))
        name = self._extract_name(content).replace('\n', '')
        keywords = self._extract_keywords(content)

        entry = {'url': url, 'keywords': set(), 'aliases': set()}
        self.results[name].append(entry)

        for n in self._parse_title(name):
            """ add as keyword """
            entry["keywords"].add(n)

            """ add as keyword without std:: """
            if n.find("std::") != -1:
                entry["keywords"].add(n.replace('std::', ''))

            """ add with all keywords variations """
            for k in keywords:
                """ add std:: to typedef if original type is in std namespace """
                if n.find("std::") != -1 and k.find("std::") == -1:
                    k = "std::" + k;

                entry["aliases"].add((n, k))
                prefix = _commonprefix(n, k)

                if len(prefix) > 2 and prefix[-2:] == "::":
                    """ Create names and keyword without prefixes """
                    new_name = n[len(prefix):]
                    new_key  = k[len(prefix):]
                    entry["aliases"].add((new_name, new_key))

                if k.find("std::") != -1:
                    entry["aliases"].add(
                        (n, k.replace('std::', '')))

        return True

    def _results_with_unique_title(self):
        """process crawling results and return title -> entry dictionary;
           add part of the path to entries having the same title
        """
        results = dict()
        for title, entries in self.results.items():
            if len(entries) == 1:
                results[title] = entries[0]
            else:
                paths = [_removesuffix(urlparse(entry['url'])[2], '/') for entry in entries]
                prefix = os.path.commonpath(paths)
                if prefix:
                    prefix += '/'
                suffix = '/' + os.path.basename(paths[0])
                for path in paths:
                    if not path.endswith(suffix):
                        suffix = ''
                        break
                for index, entry in enumerate(entries):
                    path = _removeprefix(paths[index], prefix)
                    path = _removesuffix(path, suffix)
                    results["{} ({})".format(title, unquote(path))] = entry
        return results

    def _extract_name(self, data):
        """Extract man page name from web page."""
        name = re.search('<[hH]1[^>]*>(.+?)</[hH]1>', data, re.DOTALL).group(1)
        name = re.sub(r'<([^>]+)>', r'', name)
        name = re.sub(r'&gt;', r'>', name)
        name = re.sub(r'&lt;', r'<', name)
        return html.unescape(name)

    def _parse_expression(self, expr):
        """
            split expression into prefix and expression
            tested with
            ```
            operator==
            !=
            std::rel_ops::operator!=
            std::atomic::operator=
            std::array::operator[]
            std::function::operator()
            std::vector::at
            std::relational operators
            std::vector::begin
            std::abs(float)
            std::fabs()
            ```
        """
        m = re.match(r'^(.*?(?:::)?(?:operator)?)((?:::[^:]*|[^:]*)?)$', expr)
        prefix = m.group(1)
        tail = m.group(2)
        return [prefix, tail]

    def _parse_title(self, title):
        """
             split of the last parenthesis  operator==,!=,<,<=(std::vector)
             tested with
            ```
            operator==,!=,<,<=,>,>=(std::vector)
            operator==,!=,<,<=,>,>=(std::vector)
            operator==,!=,<,<=,>,>=
            operator==,!=,<,<=,>,>=
            std::rel_ops::operator!=,>,<=,>=
            std::atomic::operator=
            std::array::operator[]
            std::function::operator()
            std::vector::at
            std::relational operators (vector)
            std::vector::begin, std::vector::cbegin
            std::abs(float), std::fabs
            std::unordered_set::begin(size_type), std::unordered_set::cbegin(size_type)
            ```
        """
        """ remove all template stuff """
        title = re.sub(r" ?<[^>]+>", "", title)

        m = re.match(
            r'^\s*((?:\(size_type\)|(?:.|\(\))*?)*)((?:\([^)]+\))?)\s*$', title)

        postfix = m.group(2)

        t_names = m.group(1).split(',')
        t_names = [n.strip() for n in t_names]
        prefix = self._parse_expression(t_names[0])[0]
        names = []
        for n in t_names:
            r = self._parse_expression(n)
            if prefix == r[0]:
                names.append(n + postfix)
            else:
                names.append(prefix + r[1] + postfix)
        return names

    def _extract_keywords(self, text):
        """
            extract aliases like std::string, template specializations like std::atomic_bool
            and helper functions like std::is_same_v
        """
        soup = BeautifulSoup(text, "lxml")
        names = []

        # search for typedef list
        for x in soup.find_all('table'):
            # just searching for "Type" is not enough, see std::is_same
            p = x.find_previous_sibling('h3')
            if p:
                if p.get_text().strip() == "Member types":
                    continue

            typedefTable = False
            for tr in x.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) == 2:
                    if re.match("\s*Type\s*", tds[0].get_text()):
                        typedefTable = True
                    elif typedefTable:
                        res = re.search('^\s*(\S*)\s+.*$', tds[0].get_text())
                        if res and res.group(1):
                            names.append(res.group(1))
                    elif not typedefTable:
                        break
            if typedefTable:
                break

        # search for "Helper variable template" list
        for x in soup.find_all('h3'):
            variableTemplateHeader = False
            if x.find('span', id="Helper_variable_template"):
                e = x.find_next_sibling()
                while e.name == "":
                    e = e.find_next_sibling()
                if e.name == "table":
                    for tr in e.find_all('tr'):
                        text = re.sub('\n', ' ', tr.get_text())
                        res = re.search('^.* (\S+)\s*=.*$', text)
                        if res:
                            names.append(res.group(1))
        # search for "Helper types" list
        for x in soup.find_all('h3'):
            variableTemplateHeader = False
            if x.find('span', id="Helper_types"):
                e = x.find_next_sibling()
                while e.name == "":
                    e = e.find_next_sibling()
                if e.name == "table":
                    for tr in e.find_all('tr'):
                        text = re.sub('\n', ' ', tr.get_text())
                        res = re.search('^.* (\S+)\s*=.*$', text)
                        if res:
                            names.append(res.group(1))
        return [html.unescape(n) for n in names]

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
        data = cursor.execute('SELECT title, url FROM "%s"' % source).fetchall()

        for name, url in data:
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

        formatter = importlib.import_module(
            'cppman.formatter.%s' % source[:-4])
        groff_text = formatter.html2groff(data, name)

        with gzip.open(outname, 'w') as f:
            f.write(groff_text.encode('utf-8'))

    def clear_cache(self):
        """Clear all cache in man"""
        shutil.rmtree(environ.cache_dir)

    def _fetch_page_by_keyword(self, keyword):
        """ fetches result for a keyword """
        return self.cursor.execute(
            'SELECT t1.title, t2.keyword, t1.url '
            'FROM "%s" AS t1 '
            'JOIN "%s_keywords" AS t2 '
            'WHERE t1.id = t2.id AND t2.keyword '
            'LIKE ? ORDER BY t2.keyword'
            % (self.source, self.source), ['%%%s%%' % keyword]).fetchall()

    def _search_keyword(self, pattern):
        """ multiple fetches for each pattern """
        if not os.path.exists(environ.index_db):
            raise RuntimeError("can't find index.db")

        conn = sqlite3.connect(environ.index_db)
        self.cursor = conn.cursor()
        self.source = environ.source

        self.cursor.execute('PRAGMA case_sensitive_like=ON')
        results = self._fetch_page_by_keyword("%s" % pattern)
        results.extend(self._fetch_page_by_keyword("%s %%" % pattern))
        results.extend(self._fetch_page_by_keyword("%% %s" % pattern))
        results.extend(self._fetch_page_by_keyword("%% %s %%" % pattern))

        results.extend(self._fetch_page_by_keyword("%s%%" % pattern))
        if len(results) == 0:
            results = self._fetch_page_by_keyword("%%%s%%" % pattern)

        conn.close()
        return sorted(list(set(results)), key=lambda e: _sort_search(e, pattern))

    def man(self, pattern):
        """Call viewer.sh to view man page"""
        results = self._search_keyword(pattern)
        if len(results) == 0:
            raise RuntimeError('No manual entry for %s ' % pattern)

        page_name, keyword, url = results[0]

        try:
            avail = os.listdir(os.path.join(environ.cache_dir, environ.source))
        except OSError:
            avail = []

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
                     str(columns), environ.pager_config, pattern)
        return pid

    def find(self, pattern):
        """Find pages in database."""

        results = self._search_keyword(pattern)

        pat = re.compile('(.*?)(%s)(.*?)( \(.*\))?$' %
                         re.escape(pattern), re.I)

        if results:
            for name, keyword, url in results:

                if os.isatty(sys.stdout.fileno()):
                    keyword = pat.sub(
                        r'\1\033[1;31m\2\033[0m\3\033[1;33m\4\033[0m', keyword)
                print("%s - %s" % (keyword, name))
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
