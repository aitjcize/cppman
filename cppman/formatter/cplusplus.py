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
import urllib.request

from cppman.formatter.tableparser import parse_table
from cppman.util import fixupHTML, html2man

# Format replacement RE list
# The '.SE' pseudo macro is described in the function: html2groff
pre_rps = [
    # Snippet, ugly hack: we don't want to treat code listing as table
    (r'<table class="snippet">(.*?)</table>',
     r'\n.in +2n\n\1\n.in\n.sp\n', re.S),
]

rps = [
    # Header, Name
    (r'\s*<div id="I_type"[^>]*>(.*?)\s*</div>\s*'
     r'<div id="I_file"[^>]*>(.*?)</div>\s*'
     r'<h1>(.*?)</h1>\s*<div class="C_prototype"[^>]*>'
     r'(.*?)</div>\s*<div id="I_description"[^>]*>(.*?)</div>',
     r'.TH "\3" 3 "%s" "cplusplus.com" "C++ Programmer\'s Manual"\n'
     r'\n.SH "NAME"\n\3 - \5\n'
     r'\n.SE\n.SH "TYPE"\n\1\n'
     r'\n.SE\n.SH "SYNOPSIS"\n#include \2\n.sp\n\4\n'
     r'\n.SE\n.SH "DESCRIPTION"\n' % datetime.date.today(), re.S),
    (r'\s*<div id="I_type"[^>]*>(.*?)\s*</div>\s*'
     r'<div id="I_file"[^>]*>(.*?)</div>\s*'
     r'<h1>(.*?)</h1>\s*'
     r'<div id="I_description"[^>]*>(.*?)</div>',
     r'.TH "\3" 3 "%s" "cplusplus.com" "C++ Programmer\'s Manual"\n'
     r'\n.SH "NAME"\n\3 - \4\n'
     r'\n.SE\n.SH "TYPE"\n\1\n'
     r'\n.SE\n.SH "SYNOPSIS"\n#include \2\n.sp\n'
     r'\n.SE\n.SH "DESCRIPTION"\n' % datetime.date.today(), re.S),
    (r'\s*<div id="I_type"[^>]*>(.*?)\s*</div>\s*<h1>(.*?)</h1>\s*'
     r'<div id="I_description"[^>]*>(.*?)</div>',
     r'.TH "\2" 3 "%s" "cplusplus.com" "C++ Programmer\'s Manual"\n'
     r'\n.SH "NAME"\n\2 - \3\n'
     r'\n.SE\n.SH "TYPE"\n\1\n'
     r'\n.SE\n.SH "DESCRIPTION"\n' % datetime.date.today(), re.S),
    (r'\s*<div id="I_type"[^>]*>(.*?)\s*</div>\s*<h1>(.*?)</h1>\s*'
     r'<div id="I_file"[^>]*>(.*?)</div>\s*<div id="I_description"[^>]*>'
     '(.*?)</div>',
     r'.TH "\2" 3 "%s" "cplusplus.com" "C++ Programmer\'s Manual"\n'
     r'\n.SH "NAME"\n\2 - \4\n'
     r'\n.SE\n.SH "TYPE"\n\1\n'
     r'\n.SE\n.SH "DESCRIPTION"\n' % datetime.date.today(), re.S),
    (r'\s*<div id="I_type"[^>]*>(.*?)\s*</div>\s*<h1>(.*?)</h1>\s*'
     r'<div class="C_prototype"[^>]*>(.*?)</div>\s*'
     r'<div id="I_description"[^>]*>(.*?)</div>',
     r'.TH "\2" 3 "%s" "cplusplus.com" "C++ Programmer\'s Manual"\n'
     r'\n.SH "NAME"\n\2 - \4\n'
     r'\n.SE\n.SH "TYPE"\n\1\n'
     r'\n.SE\n.SH "SYNOPSIS"\n\3\n'
     r'\n.SE\n.SH "DESCRIPTION"\n' % datetime.date.today(), re.S),
    (r'<span alt="[^"]*?" class="C_ico cpp11warning"[^>]*>',
     r' [C++11]', re.S),
    # Remove empty #include
    (r'#include \n.sp\n', r'', 0),
    # Remove empty sections
    (r'\n.SH (.+?)\n+.SE', r'', 0),
    # Section headers
    (r'.*<h3>(.+?)</h3>', r'\n.SE\n.SH "\1"\n', 0),
    # 'ul' tag
    (r'<ul>', r'\n.RS 2\n', 0),
    (r'</ul>', r'\n.RE\n.sp\n', 0),
    # 'li' tag
    (r'<li>\s*(.+?)</li>', r'\n.IP \[bu] 3\n\1\n', re.S),
    # 'pre' tag
    (r'<pre[^>]*>(.+?)</pre\s*>', r'\n.nf\n\1\n.fi\n', re.S),
    # Subsections
    (r'<b>(.+?)</b>:<br/>', r'.SS \1\n', 0),
    # Member functions / See Also table
    # Without C++11 tag
    (r'<dl class="links"><dt><a href="[^"]*"><b>([^ ]+?)</b></a></dt><dd>'
     r'([^<]*?)<span class="typ">\s*\(([^<]*?)\n?\)</span></dd></dl>',
     r'\n.IP "\1 (3)"\n\2 (\3)\n', re.S),
    # With C++11 tag
    (r'<dl class="links"><dt><a href="[^"]*"><b>([^ ]+?) <b class="C_cpp11" '
     r'title="(.+?)"></b></b></a></dt><dd>'
     r'([^<]*?)<span class="typ">\s*\((.*?)\n?\)</span></dd></dl>',
     r'\n.IP "\1 (3) [\2]"\n\3 (\4)\n', re.S),
    # Footer
    (r'<div id="CH_bb">.*$',
     r'\n.SE\n.SH "REFERENCE"\n'
     r'cplusplus.com, 2000-2015 - All rights reserved.', re.S),
    # C++ version tag
    (r'<div.+?title="(C\+\+..)"[^>]*>', r'.sp\n\1\n', 0),
    # 'br' tag
    (r'<br/>', r'\n.br\n', 0),
    (r'\n.br\n.br\n', r'\n.sp\n', 0),
    # 'dd' 'dt' tag
    (r'<dt>(.+?)</dt>\s*<dd>(.+?)</dd>', r'.IP "\1"\n\2\n', re.S),
    # Bold
    (r'<strong>(.+?)</strong>', r'\n.B \1\n', 0),
    # Remove row number in EXAMPLE
    (r'<td class="rownum">.*?</td>', r'', re.S),
    # Any other tags
    (r'<script[^>]*>[^<]*</script>', r'', 0),
    (r'<.*?>', r'', re.S),
    # Misc
    (r'&lt;', r'<', 0),
    (r'&gt;', r'>', 0),
    (r'&quot;', r'"', 0),
    (r'&amp;', r'&', 0),
    (r'&nbsp;', r' ', 0),
    (r'\\([^\^nE])', r'\\\\\1', 0),
    (r'>/">', r'', 0),
    (r'/">', r'', 0),
    # Remove empty lines
    (r'\n\s*\n+', r'\n', 0),
    (r'\n\n+', r'\n', 0),
    # Preserve \n" in EXAMPLE
    (r'\\n', r'\\en', 0),
]


def escape_pre_section(table):
    """Escape <pre> section in table."""
    def replace_newline(g):
        return g.group(1).replace('\n', '\n.br\n')

    return re.sub('<pre.*?>(.*?)</pre>', replace_newline, table, flags=re.S)


def html2groff(data, name):
    """Convert HTML text from cplusplus.com to Groff-formatted text."""
    # Remove sidebar
    try:
        data = data[data.index('<div class="C_doc">'):]
    except ValueError:
        pass

    # Pre replace all
    for rp in pre_rps:
        data = re.compile(rp[0], rp[2]).sub(rp[1], data)

    for table in re.findall(r'<table.*?>.*?</table>', data, re.S):
        tbl = parse_table(escape_pre_section(table))
        # Escape column with '.' as prefix
        tbl = re.compile(r'T{\n(\..*?)\nT}', re.S).sub(r'T{\n\\E \1\nT}', tbl)
        data = data.replace(table, tbl)

    # Replace all
    for rp in rps:
        data = re.compile(rp[0], rp[2]).sub(rp[1], data)

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

    page_type = re.search(r'\n\.SH "TYPE"\n(.+?)\n', data)
    if page_type and 'class' in page_type.group(1):
        class_name = re.search(
            r'\n\.SH "NAME"\n(?:.*::)?(.+?) ', data).group(1)

        secs = re.findall(r'\n\.SH "(.+?)"(.+?)\.SE', data, re.S)

        for sec, content in secs:
            # Member functions
            if ('MEMBER' in sec and
                'NON-MEMBER' not in sec and
                'INHERITED' not in sec and
                    sec != 'MEMBER TYPES'):
                content2 = re.sub(r'\n\.IP "([^:]+?)"', r'\n.IP "%s::\1"'
                                  % class_name, content)
                # Replace (constructor) (destructor)
                content2 = re.sub(r'\(constructor\)', r'%s' % class_name,
                                  content2)
                content2 = re.sub(r'\(destructor\)', r'~%s' % class_name,
                                  content2)
                data = data.replace(content, content2)
            # Inherited member functions
            elif 'MEMBER' in sec and 'INHERITED' in sec:
                inherit = re.search(r'.+?INHERITED FROM (.+)',
                                    sec).group(1).lower()
                content2 = re.sub(r'\n\.IP "(.+)"', r'\n.IP "%s::\1"'
                                  % inherit, content)
                data = data.replace(content, content2)

    # Remove pseudo macro '.SE'
    data = data.replace('\n.SE', '')

    return data


def func_test():
    """Test if there is major format changes in cplusplus.com"""
    ifs = urllib.request.urlopen('http://www.cplusplus.com/printf')
    result = html2groff(fixupHTML(ifs.read()), 'printf')
    assert '.SH "NAME"' in result
    assert '.SH "TYPE"' in result
    assert '.SH "DESCRIPTION"' in result


def test():
    """Simple Text"""
    ifs = urllib.request.urlopen('http://www.cplusplus.com/vector')
    print(html2groff(fixupHTML(ifs.read()), 'std::vector'), end=' ')
    # with open('test.html') as ifs:
    #    print html2groff(fixupHTML(ifs.read()), 'std::vector'),


if __name__ == '__main__':
    test()
