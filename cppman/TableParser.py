#!/usr/bin/env python

import re
import sys
import StringIO

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
        print '%s%s: %s' % (' ' * depth, self.name, self.text)

        for c in self.children:
            c.traverse(depth + 2)

    def scan_format(self, index=0, total=0, rowspan={}):
        format_str = ''

        if self.name in ['th', 'td']:
            if self.attr.has_key('colspan'):
                total += int(self.attr['colspan']) - 1

            extend = ((total == 3 and index == 1) or
                      (total != 3 and total < 5 and index == total -1))

            if self.name == 'th':
                format_str += 'c%s ' % ('x' if extend else '')
            else:
                format_str += 'l%s ' % ('x' if extend else '')

            if self.attr.has_key('colspan'):
                for i in range(int(self.attr['colspan']) - 1):
                    format_str += 's '

            if self.attr.has_key('rowspan'):
                rowspan[index] = int(self.attr['rowspan']) - 1

        if self.name == 'tr' and len(rowspan) > 0:
            total = len(rowspan) + len(self.children)
            ci = 0
            for i in range(total):
                if rowspan.has_key(i):
                    format_str += '^ '
                    if rowspan[i] == 1:
                        del rowspan[i]
                    else:
                        rowspan[i] -= 1
                else:
                    format_str += self.children[ci].scan_format(i,
                            total, rowspan)
                    ci += 1
        else:
            for i, c in enumerate(self.children):
                format_str += c.scan_format(i, len(self.children), rowspan)

        if self.name == 'table':
            format_str += '.\n'
        elif self.name == 'tr':
            format_str += '\n'

        return format_str

    def gen(self, fd, index=0, last=False, rowspan={}):
        if self.name == 'table':
            fd.write('.TS\n')
            fd.write('allbox tab(|);\n')
            fd.write(self.scan_format())
        elif self.name in ['th', 'td']:
            fd.write('T{\n%s' % self.text)
            if self.attr.has_key('rowspan'):
                rowspan[index] = int(self.attr['rowspan']) - 1
        else:
            fd.write(self.text)

        if self.name == 'tr' and len(rowspan) > 0:
            total = len(rowspan) + len(self.children)
            ci = 0
            for i in range(total):
                if rowspan.has_key(i):
                    fd.write('\^%s' % ('|' if i < total - 1 else ''))
                    if rowspan[i] == 1:
                        del rowspan[i]
                    else:
                        rowspan[i] -= 1
                else:
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
    fd = StringIO.StringIO()
    root.gen(fd)
    return fd.getvalue()
