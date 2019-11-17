# -*- coding: utf-8 -*-
#
# tableparser.py - format html from cplusplus.com to groff syntax
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

import io
import platform
import re

NODE = re.compile(r'<\s*([^/]\w*)\s?(.*?)>(.*?)<\s*/\1.*?>', re.S)
ATTR = re.compile(r'\s*(\w+?)\s*=\s*([\'"])((?:\\.|(?!\2).)*)\2')


class Node(object):
    def __init__(self, parent, name, attr_list, body):
        self.parent = parent
        self.name = name
        self.body = body
        self.attr = dict((x[0], x[2]) for x in ATTR.findall(attr_list))

        if self.name in ['th', 'td']:
            self.text = self.strip_tags(self.body)
            self.children = []
        else:
            self.text = ''
            self.children = [Node(self, *g) for g in NODE.findall(self.body)]

    def __repr__(self):
        return "<Node('%s')>" % self.name

    def strip_tags(self, html):
        if type(html) != str:
            html = html.group(3)
        return NODE.sub(self.strip_tags, html)

    def traverse(self, depth=0):
        print('%s%s: %s %s' % (' ' * depth, self.name, self.attr, self.text))

        for c in self.children:
            c.traverse(depth + 2)

    def get_row_width(self):
        total = 0
        assert self.name == 'tr'
        for c in self.children:
            if 'colspan' in c.attr:
                total += int(c.attr['colspan'])
            else:
                total += 1
        return total

    def scan_format(self, index=0, width=0, rowspan=None):
        if rowspan is None:
            rowspan = {}

        format_str = ''

        expand_char = 'x' if platform.system() != 'Darwin' else ''

        if self.name in ['th', 'td']:
            extend = ((width == 3 and index == 1) or
                      (width != 3 and width < 5 and index == width - 1))

            if self.name == 'th':
                format_str += 'c%s ' % (expand_char if extend else '')
            else:
                format_str += 'l%s ' % (expand_char if extend else '')

            if 'colspan' in self.attr:
                for i in range(int(self.attr['colspan']) - 1):
                    format_str += 's '

            if 'rowspan' in self.attr and int(self.attr['rowspan']) > 1:
                rowspan[index] = int(self.attr['rowspan']) - 1

        if self.name == 'tr' and len(rowspan) > 0:
            ci = 0
            for i in range(width):
                if i in rowspan:
                    format_str += '^ '
                    if rowspan[i] == 1:
                        del rowspan[i]
                    else:
                        rowspan[i] -= 1
                else:
                    # There is a row span, but the current number of column is
                    # not enough. Pad empty node when this happens.
                    if ci >= len(self.children):
                        self.children.append(Node(self, 'td', '', ''))

                    format_str += self.children[ci].scan_format(i, width,
                                                                rowspan)
                    ci += 1
        else:
            if self.children and self.children[0].name == 'tr':
                width = self.children[0].get_row_width()

            for i, c in enumerate(self.children):
                format_str += c.scan_format(i, width, rowspan)

        if self.name == 'table':
            format_str += '.\n'
        elif self.name == 'tr':
            format_str += '\n'

        return format_str

    def gen(self, fd, index=0, last=False, rowspan=None):
        if rowspan is None:
            rowspan = {}

        if self.name == 'table':
            fd.write('.TS\n')
            fd.write('allbox tab(|);\n')
            fd.write(self.scan_format())
        elif self.name in ['th', 'td']:
            fd.write('T{\n%s' % self.text)
            if 'rowspan' in self.attr and int(self.attr['rowspan']) > 1:
                rowspan[index] = int(self.attr['rowspan']) - 1
        else:
            fd.write(self.text)

        if self.name == 'tr' and len(rowspan) > 0:
            total = len(rowspan) + len(self.children)
            ci = 0
            for i in range(total):
                if i in rowspan:
                    fd.write('\^%s' % ('|' if i < total - 1 else ''))
                    if rowspan[i] == 1:
                        del rowspan[i]
                    else:
                        rowspan[i] -= 1
                else:
                    # There is a row span, but the current number of column is
                    # not enough. Pad empty node when this happens.
                    if ci >= len(self.children):
                        self.children.append(Node(self, 'td', '', ''))

                    self.children[ci].gen(fd, i, i == total - 1, rowspan)
                    ci += 1
        else:
            for i, c in enumerate(self.children):
                c.gen(fd, i, i == len(self.children) - 1, rowspan)

        if self.name == 'table':
            fd.write('.TE\n')
            fd.write('.sp\n.sp\n')
        elif self.name == 'tr':
            fd.write('\n')
        elif self.name in ['th', 'td']:
            fd.write('\nT}%s' % ('|' if not last else ''))


def parse_table(html):
    root = Node(None, 'root', '', html)
    fd = io.StringIO()
    root.gen(fd)
    return fd.getvalue()
