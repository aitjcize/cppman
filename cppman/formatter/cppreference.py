# -*- coding: utf-8 -*-
#
# formatter.py - format html from cplusplus.com to groff syntax
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

import datetime
import re
import string
import urllib.request
from functools import partial

from cppman.formatter.tableparser import parse_table
from cppman.util import fixupHTML, html2man


def member_table_def(g):
    tbl = parse_table('<table>%s</table>' % str(g.group(3)))
    # Escape column with '.' as prefix
    tbl = re.compile(r'T{\n(\..*?)\nT}', re.S).sub(r'T{\n\\E \1\nT}', tbl)
    return '\n.IP "%s"\n%s\n%s\n' % (g.group(1), g.group(2), tbl)


def member_type_function(g):
    if g.group(1).find("<a href=") == -1:
        return ""
    head = re.sub(r'<.*?>', '', g.group(1)).strip()
    tail = ''
    cppvertag = re.search(
        '^(.*?)(\[(?:(?:since|until) )?C\+\+\d+\]\s*(,\s*)?)+$', head)
    if cppvertag:
        head = cppvertag.group(1).strip()
        tail = ' ' + cppvertag.group(2)

    if ',' in head:
        head = ', '.join([x.strip() + ' (3)' for x in head.split(',')])
    else:
        head = head.strip() + ' (3)'
    full = (head + tail).replace('"', '\\(dq')
    """ remove [static] tag as in string::npos[static] """
    full = full.replace("[static]", "");
    return '\n.IP "%s"\n%s\n' % (full, g.group(2))


NAV_BAR_END = '<div class="t-navbar-sep">.?</div></div>'

# Format replacement RE list
# The '.SE' pseudo macro is described in the function: html2groff
rps = [
    # Workaround: remove <p> in t-dcl
    (r'<tr class="t-dcl">(.*?)</tr>',
     lambda g: re.sub('<p/?>', '', g.group(1)), re.S),
    # Header, Name
    (r'<h1.*?>(.*?)</h1>',
     r'\n.TH "{{name}}" 3 "%s" "cppreference.com" "C++ Programmer\'s Manual"\n'
     r'\n.SH "NAME"\n{{name}} {{shortdesc}}\n.SE\n' % datetime.date.today(),
     re.S),
    # Defined in header
    (r'<div class="t-navbar"[^>]*>.*?' + NAV_BAR_END + r'.*?'
     r'Defined in header <code>(.*?)</code>(.*?)<tr class="t-dcl-sep">',
     r'\n.SH "SYNOPSIS"\n#include \1\n.sp\n'
     r'.nf\n\2\n.fi\n.SE\n'
     r'\n.SH "DESCRIPTION"\n', re.S),
    (r'<div class="t-navbar"[^>]*>.*?' + NAV_BAR_END +
     r'(.*?)<tr class="t-dcl-sep">',
     r'\n.SH "SYNOPSIS"\n.nf\n\1\n.fi\n.SE\n'
     r'\n.SH "DESCRIPTION"\n', re.S),
    # <unordered_map>
    (r'<div class="t-navbar"[^>]*>.*?' + NAV_BAR_END +
     r'(.*?)<table class="t-dsc-begin">',
     r'\n.SH "DESCRIPTION"\n\1\n', re.S),
    # access specifiers
    (r'<div class="t-navbar"[^>]*>.*?' + NAV_BAR_END +
     r'(.*?)<h3',
     r'\n.SH "DESCRIPTION"\n\1\n<h3', re.S),
    (r'<td>\s*\([0-9]+\)\s*</td>', r'', 0),
    # Section headers
    (r'<div class="t-inherited">.*?<h2>.*?Inherited from\s*(.*?)\s*</h2>',
     r'\n.SE\n.IEND\n.IBEGIN \1\n', re.S),
    # Remove tags
    (r'<span class="edit.*?">.*?</span> ?', r'', re.S),
    (r'&#91;edit&#93;', r'', re.S),
    (r'\[edit\]', r'', re.S),
    (r'<div id="siteSub">.*?</div>', r'', 0),
    (r'<div id="contentSub">.*?</div>', r'', 0),
    (r'<table class="toc" id="toc"[^>]*>.*?</table>', r'', re.S),
    (r'<h2[^>]*>.*?</h2>', r'', re.S),
    (r'<div class="coliru-btn coliru-btn-run-init">.*?</div>', r'', re.S),
    (r'<tr class="t-dsc-hitem">.*?</tr>', r'', re.S),
    # C++11/14/17/20
    (r'\(((?:since|until) C\+\+\d+)\)', r' [\1]', re.S),
    (r'\((C\+\+\d+)\)', r' [\1]', re.S),
    # Subsections
    (r'<h5[^>]*>\s*(.*)</h5>', r'\n.SS "\1"\n', 0),
    # Group t-lines
    (r'<span></span>', r'', re.S),
    (r'<span class="t-lines">(?:<span>.+?</span>.*)+</span>',
     lambda x: re.sub('\s*</span><span>\s*', r', ', x.group(0)), re.S),
    # Member type & function second col is group see basic_fstream for example
    (r'<tr class="t-dsc">\s*?<td>((?:(?!</td>).)*?)</td>\s*?'
     r'<td>((?:(?!</td>).)*?)<table[^>]*>((?:(?!</table>).)*?)</table>'
     r'(?:(?!</td>).)*?</td>\s*?</tr>',
     member_table_def, re.S),
    # Section headers
    (r'.*<h3>(.+?)</h3>', r'\n.SE\n.SH "\1"\n', 0),
    # Member type & function
    (r'<tr class="t-dsc">\n?<td>\s*(.*?)\n?</td>.*?<td>\s*(.*?)</td>.*?</tr>',
     member_type_function, re.S),
    # Parameters
    (r'<tr class="t-par">.*?<td>\s*(.*?)\n?</td>.*?<td>.*?</td>.*?'
     r'<td>\s*(.*?)</td>.*?</tr>',
     r'\n.IP "\1"\n\2\n', re.S),
    # 'ul' tag
    (r'<ul>', r'\n.RS 2\n', 0),
    (r'</ul>', r'\n.RE\n.sp\n', 0),
    # 'li' tag
    (r'<li>\s*(.+?)</li>', r'\n.IP \[bu] 3\n\1\n', re.S),
    # 'pre' tag
    (r'<pre[^>]*>(.+?)</pre\s*>', r'\n.in +2n\n.nf\n\1\n.fi\n.in\n', re.S),
    # Footer
    (r'<div class="printfooter">',
     r'\n.SE\n.IEND\n.SH "REFERENCE"\n'
     r'cppreference.com, 2015 - All rights reserved.', re.S),
    # C++ version tag
    (r'<div title="(C\+\+..)"[^>]*>', r'.sp\n\1\n', 0),
    # Output
    (r'<p>Output:\n?</p>', r'\n.sp\nOutput:\n', re.S),
    # Paragraph
    (r'<p>(.*?)</p>', r'\n\1\n.sp\n', re.S),
    (r'<div class="t-li1">(.*?)</div>', r'\n\1\n.sp\n', re.S),
    (r'<div class="t-li2">(.*?)</div>',
     r'\n.RS\n\1\n.RE\n.sp\n', re.S),
    # 'br' tag
    (r'<br/>', r'\n.br\n', 0),
    (r'\n.br\n.br\n', r'\n.sp\n', 0),
    # 'dd' 'dt' tag
    (r'<dt>(.+?)</dt>\s*<dd>(.+?)</dd>', r'\n.IP "\1"\n\2\n', re.S),
    # Bold
    (r'<strong>(.+?)</strong>', r'\n.B \1\n', 0),
    # Any other tags
    (r'<script[^>]*>[^<]*</script>', r'', 0),
    (r'<.*?>', r'', re.S),
    # Escape
    (r'^#', r'\#', 0),
    (r'&#160;', ' ', 0),
    (r'&#(\d+);', lambda g: chr(int(g.group(1))), 0),
    # Misc
    (r'&lt;', r'<', 0),
    (r'&gt;', r'>', 0),
    (r'&quot;', r'"', 0),
    (r'&amp;', r'&', 0),
    (r'&nbsp;', r' ', 0),
    (r'\\([^\^nE])', r'\\\\\1', 0),
    (r'>/">', r'', 0),
    (r'/">', r'', 0),
    # Remove empty sections
    (r'\n.SH (.+?)\n+.SE', r'', 0),
    # Remove empty lines
    (r'\n\s*\n+', r'\n', 0),
    (r'\n\n+', r'\n', 0),
    # Preserve \n" in EXAMPLE
    (r'\\n', r'\\en', 0),
    # Remove leading whitespace
    (r'^\s+', r'', re.S),
    # Trailing white-spaces
    (r'\s+\n', r'\n', re.S),
    # Remove extra whitespace and newline in .SH/SS/IP section
    (r'.(SH|SS|IP) "\s*(.*?)\s*\n?"', r'.\1 "\2"', 0),
    # Remove extra whitespace before .IP bullet
    (r'(.IP \\\\\[bu\] 3)\n\s*(.*?)\n', r'\1\n\2\n', 0),
    # Remove extra '\n' before C++ version Tag (don't do it in table)
    (r'(?<!T{)\n\s*(\[(:?since|until) C\+\+\d+\])', r' \1', re.S)
]


def html2groff(data, name):
    """Convert HTML text from cppreference.com to Groff-formatted text."""
    # Remove header and footer
    try:
        data = data[data.index('<div id="cpp-content-base">'):]
        data = data[:data.index('<div class="printfooter">') + 25]
    except ValueError:
        pass

    # Remove non-printable characters
    data = ''.join([x for x in data if x in string.printable])

    for table in re.findall(
            r'<table class="(?:wikitable|dsctable)"[^>]*>.*?</table>',
            data, re.S):
        tbl = parse_table(table)
        # Escape column with '.' as prefix
        tbl = re.compile(r'T{\n(\..*?)\nT}', re.S).sub(r'T{\n\\E \1\nT}', tbl)
        data = data.replace(table, tbl)

    # Pre replace all
    for rp in rps:
        data = re.compile(rp[0], rp[2]).sub(rp[1], data)

    # Remove non-printable characters
    data = ''.join([x for x in data if x in string.printable])

    # Upper case all section headers
    for st in re.findall(r'.SH .*\n', data):
        data = data.replace(st, st.upper())

    # Add tags to member/inherited member functions
    # e.g. insert -> vector::insert
    #
    # .SE is a pseudo macro I created which means 'SECTION END'
    # The reason I use it is because I need a marker to know where section
    # ends.
    # re.findall find patterns which does not overlap, which means if I do
    # this: secs = re.findall(r'\n\.SH "(.+?)"(.+?)\.SH', data, re.S)
    # re.findall will skip the later .SH tag and thus skip the later section.
    # To fix this, '.SE' is used to mark the end of the section so the next
    # '.SH' can be find by re.findall

    try:
        idx = data.index('.IEND')
    except ValueError:
        idx = None

    def add_header_multi(prefix, g):
        if ',' in g.group(1):
            res = ', '.join(['%s::%s' % (prefix, x.strip())
                             for x in g.group(1).split(',')])
        else:
            res = '%s::%s' % (prefix, g.group(1))

        return '\n.IP "%s"' % res

    if idx:
        class_name = name
        if class_name.startswith('std::'):
            normalized_class_name = class_name[len('std::'):]
        else:
            normalized_class_name = class_name
        class_member_content = data[:idx]
        secs = re.findall(r'\.SH "(.+?)"(.+?)\.SE', class_member_content, re.S)

        for sec, content in secs:
            # Member functions
            if (('MEMBER' in sec and
                'NON-MEMBER' not in sec and
                'INHERITED' not in sec and
                'MEMBER TYPES' != sec) or
                'CONSTANTS' == sec):
                content2 = re.sub(r'\n\.IP "([^:]+?)"',
                                  partial(add_header_multi, class_name),
                                  content)
                # Replace (constructor) (destructor)
                content2 = re.sub(r'\(constructor\)', r'%s' %
                                  normalized_class_name, content2)
                content2 = re.sub(r'\(destructor\)', r'~%s' %
                                  normalized_class_name, content2)
                data = data.replace(content, content2)

    blocks = re.findall(r'\.IBEGIN\s*(.+?)\s*\n(.+?)\.IEND', data, re.S)

    for inherited_class, content in blocks:
        content2 = re.sub(r'\.SH "(.+?)"', r'\n.SH "\1 INHERITED FROM %s"'
                          % inherited_class.upper(), content)
        data = data.replace(content, content2)

        secs = re.findall(r'\.SH "(.+?)"(.+?)\.SE', content, re.S)

        for sec, content in secs:
            # Inherited member functions
            if 'MEMBER' in sec and \
               sec != 'MEMBER TYPES':
                content2 = re.sub(r'\n\.IP "(.+)"',
                                  partial(add_header_multi, inherited_class),
                                  content)
                data = data.replace(content, content2)

    # Remove unneeded pseudo macro
    data = re.sub('(?:\n.SE|.IBEGIN.*?\n|\n.IEND)', '', data)

    # Replace all macros
    desc_re = re.search(r'.SH "DESCRIPTION"\n.*?([^\n\s].*?)\n', data)
    shortdesc = ''

    # not empty description
    if desc_re and not desc_re.group(1).startswith('.SH'):
        shortdesc = '- ' + desc_re.group(1)

    def dereference(g):
        d = dict(name=name, shortdesc=shortdesc)
        if g.group(1) in d:
            return d[g.group(1)]

    data = re.sub('{{(.*?)}}', dereference, data)

    return data


def func_test():
    """Test if there is major format changes in cplusplus.com"""
    ifs = urllib.request.urlopen(
        'http://en.cppreference.com/w/cpp/container/vector')
    result = html2groff(fixupHTML(ifs.read()), 'std::vector')
    assert '.SH "NAME"' in result
    assert '.SH "SYNOPSIS"' in result
    assert '.SH "DESCRIPTION"' in result


def test():
    """Simple Text"""
    ifs = urllib.request.urlopen(
        'http://en.cppreference.com/w/cpp/container/vector')
    print(html2groff(fixupHTML(ifs.read()), 'std::vector'), end=' ')
    # with open('test.html') as ifs:
    #    data = fixupHTML(ifs.read())
    #    print html2groff(data, 'std::vector'),


if __name__ == '__main__':
    test()
