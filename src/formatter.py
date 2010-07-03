#!/usr/bin/env python
#-*- coding: utf-8 -*-
# 
# Formatter.py - format html from cplusplus.com to groff syntax
#
# Copyright (C) 2010 -  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
# All Rights reserved.
#
# This program is part of the project 'manpages-cpp'.
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

import datetime
import re
import sys
import urllib

# Format replacement RE list
rps = [
        # Header, Name
        (r'<div class="doctop"><h1>(.+?)</h1><div class="right"><br>(.+?)</div>'
         r'</div><div class="docsubtop"><div class="right">(.*)</div>\n'
         r'<div class="prototype">(.*)</div>\n</div>'
         r'<p><strong>(.+?)</strong></p>\n</div><div id="content">(.+?)<br>',
         r'.TH "\1" 3 "%s" "cplusplus" "C++ Programmer\'s Manual"\n'
         r'\n.SH NAME\n\1 - \5\n'
         r'\n.SH TYPE\n\2\n'
         r'\n.SH SYNOPSIS\n\4\n'
         r'\n.SH DESCRIPTION\n\6\n' % datetime.date.today()),
        # Remove empty sections
        (r'\n.SH (.+?)\n\n', r''),
        # Section headers
        (r'.*<h3>(.+?)</h3>', r'.SH \1\n'),
        # 'ul' tag
        (r'<ul>', r'\n.in +2n\n.sp\n'),
        (r'</ul>', r'\n.in\n'),
        # 'li' tag
        (r'<li>(.+?)</li>', r'* \1\n.sp\n'),
        # 'code' tag
        (r'<code>', r'\n.in +2n\n.sp\n'),
        (r'</code>', r'\n.in\n.sp\n'),
        # 'samp' tag
        (r'<samp>((.|\n)+?)</samp>', r'\n.nf\n\1\n.fi\n'),
        # Subsections
        (r'<b>(.+?)</b>:<br>', r'.SS \1\n'),
        # Member functions / See Also table
        (r'<div class="auto"><table class="keywordlink"><tr><td class="tit">'
         r'<a href= "[^"]*"><b>([^<]+)</b></a></td><td class="des">([^<]+)'
         r'<span class="typ">([^<]+)</span></td></tr></table></div>',
         r'.IP "\1"\n\2 \3\n'),
        # Member types table
        (r'<table class="boxed">\n<tr><th>(.+?)</th><th>(.+?)</th></tr>'
         r'((.|\n)*?)</table>',
         r'\n.TS\ncenter tab(|);\nc c\nl l .\n\1|\2\n=\n\3\n.TE\n'),
        (r'<tr><td>(.+?)</td><td>(.+?)</td></tr>', r'\1|\2\n'),
        # Snippet
        (r'<td class="rownum">.+</td>', r''),
        
        # Footer
        (r'<div id="footer">(.|\n)*</div>',
         r'\n.SH REFERENCE\ncplusplus.com, 2000-2010 - All rights reserved.'),
        # 'br' tag
        (r'<br>', r'\n.br\n'),
        # 'dd' 'dt' tag
        (r'<dt>(.+?)</dt>\s*<dd>((.|\n)+?)</dd>', r'.IP \1\n\2\n'),
        # Bold
        (r'<strong>(.+?)</strong>', r'.B \1\n'),
        # -
        (r'-', r'\-'),
        # Any other tags
        (r'<script[^>]*>[^<]*</script>', r''),
        (r'<([^>]+)>', r''),
        # Misc
        (r'&lt;', r'<'), 
        (r'&gt;', r'>'),
        (r'&amp;', r'&'),
        (r'&nbsp;', r' '),
        (u'\x0d', r'\n.br\n'),
        # Remove empty lines
        (r'\n\s*\n+', r'\n'),
        (r'\n\n+', r'\n'),
      ]

def to_groff(data):
    # Remove sidebar
    try:
        data = data[data.index('<div class="doctop"><h1>'):]
    except ValueError: pass

    # Get name
    name = re.search('<h1>(.+?)</h1>', data).group(1)
    name = re.sub(r'<([^>]+)>', r'', name)

    # Preprocess 'code' tag
    code_sections = re.findall(r'<code>.+?</code>', data, re.DOTALL)
    for cs in code_sections:
        css = re.sub(r'\n', r'\n.br\n', cs)
        index = data.index(cs)
        data = data[:index] + css + data[index + len(cs):]

    # Replace all
    for rp in rps:
        data = re.sub(rp[0], rp[1], data)

    # Upper case all section headers
    for sh in re.findall('.SH .*\n', data):
        data = re.sub(sh, sh.upper(), data)
    return name, data

def test():
    #ifs = open('index.html', 'r')
    ifs = urllib.urlopen('http://www.cplusplus.com/reference/stl/vector/')
    print to_groff(ifs.read())[1]

if __name__ == '__main__':
    test()
