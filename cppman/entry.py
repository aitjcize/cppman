# -*- coding: utf-8 -*-
#
# entry.py
#
# Copyright (C) 2010 - 2015  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
# Copyright (C) 2025  Victor Bogado da Silva Lins <victor@bogado.net>
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

import re
import html

from bs4 import BeautifulSoup
from itertools import takewhile


def _parse_expression(expr: str) -> list[str]:
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


def _commonprefix(*names: str) -> str:
    return "".join(ch[0] for ch in takewhile(
        lambda name: all(chars == name[0] for chars in names), zip(*names))
    )


class Entry(object):
    def __init__(self, url: str, content: str):
        self.url = url
        self.name = self._extract_name(content).replace('\n', '')
        self._keywords = set()
        self._parse_title(self)

    def add_keyword(self, keyword: str):
        self._keywords.add(keyword)

    def aliases(self, keyword):
        if keyword.find("std::") != -1:
            yield (keyword, keyword.replace("std::", ""))
        for other_keyword in self.keywords():
            if other_keyword == keyword:
                continue

            prefix = _commonprefix(keyword, other_keyword)
            size = len(prefix)
            if size > 2 and prefix[-2:] == "::":
                yield (keyword[size:], other_keyword[size:])

    def all_aliases(self):
        for keyword in self.keywords():
            for alias in self.aliases(keyword):
                yield alias

    def keywords(self):
        for keyword in self._keywords:
            yield keyword
            if keyword.find("std::") != -1:
                yield keyword.replace("std::", "")

    def _extract_keywords(self, text):
        """
        extract aliases like std::string, template specializations
        like std::atomic_bool and helper functions like std::is_same_v
        """
        soup = BeautifulSoup(text, "lxml")
        names = []

        # search for typedef list
        for x in soup.find_all("table"):
            # just searching for "Type" is not enough, see std::is_same
            p = x.find_previous_sibling("h3")
            if p:
                if p.get_text().strip() == "Member types":
                    continue

            typedefTable = False
            for tr in x.find_all("tr"):
                tds = tr.find_all("td")
                if len(tds) == 2:
                    if re.match(r"\s*Type\s*", tds[0].get_text()):
                        typedefTable = True
                    elif typedefTable:
                        res = re.search(r"^\s*(\S*)\s+.*$", tds[0].get_text())
                        if res and res.group(1):
                            names.append(res.group(1))
                    elif not typedefTable:
                        break
            if typedefTable:
                break

        # search for "Helper variable template" list
        for x in soup.find_all("h3"):
            if x.find("span", id="Helper_variable_template"):
                e = x.find_next_sibling()
                while e.name == "":
                    e = e.find_next_sibling()
                if e.name == "table":
                    for tr in e.find_all("tr"):
                        text = re.sub("\n", " ", tr.get_text())
                        res = re.search(r"^.* (\S+)\s*=.*$", text)
                        if res:
                            names.append(res.group(1))
        # search for "Helper types" list
        for x in soup.find_all("h3"):
            if x.find("span", id="Helper_types"):
                e = x.find_next_sibling()
                while e.name == "":
                    e = e.find_next_sibling()
                if e.name == "table":
                    for tr in e.find_all("tr"):
                        text = re.sub("\n", " ", tr.get_text())
                        res = re.search(r"^.* (\S+)\s*=.*$", text)
                        if res:
                            self.add_keyword(
                                html.unescape(
                                    names.append(
                                        res.group(1)
                                        )
                                    )
                                )

    def _extract_name(self, content: str):
        """Extract man page name from web page."""
        name = re.search('<[hH]1[^>]*>(.+?)</[hH]1>',
                         content,
                         re.DOTALL).group(1)
        name = re.sub(r'<([^>]+)>', r'', name)
        name = re.sub(r'&gt;', r'>', name)
        name = re.sub(r'&lt;', r'<', name)
        return html.unescape(name)

    def _parse_title(self, content):
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
        std::unordered_set::begin(size_type),
        std::unordered_set::cbegin(size_type)
        ```
        """
        """ remove all template stuff """
        title = re.sub(r" ?<[^>]+>", "", self.name)

        m = re.match(
            r"^\s*((?:\(size_type\)|(?:.|\(\))*?)*)((?:\([^)]+\))?)\s*$",
            re.sub(r" ?<[^>]+>", "", title)
        )

        postfix = m.group(2)

        t_names = map(lambda name: name.strip(), m.group(1).split(","))

        prefix = None
        for n in t_names:
            r = _parse_expression(n)
            if prefix is None:
                prefix = r[0]

            if prefix == r[0]:
                self.add_keyword(n + postfix)
            else:
                self.add_keyword(prefix + r[1] + postfix)
