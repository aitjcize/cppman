#!/usr/bin/env python
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

import subprocess
import formatter
import urllib
import os
from optparse import OptionParser

option_list = [
    make_option('-v', '--version', action = 'store_true', dest='version',
                default = False, help = 'Show version information'),
    make_option('-c', '--cache-all', action = 'store_true', dest='cache_all',
                default = False,
                help = 'Cache all available man pages from cplusplus.com.'),
    make_option('-k', '--clear-all', action = 'store_true', dest='clear_all',
                default = False,
                help = 'Clear all cached files.'),
    make_option('-C', '--cache-clibrary', action = 'store_true', dest='cache_c',
                default = False,
                help = 'Cache C Library (which is available in manpages-dev)'),
    make_option('-r', '--rebuild-index', action = 'store_true', dest='rindex',
                default = False,
                help = 'Cache C Library (which is available in manpages-dev)')
]

parser = OptionParser(option_list=option_list)








data = urllib.urlopen('http://www.cplusplus.com/reference/algorithm/').read()
with open('test', 'w') as f:
    f.write(formatter.cplusplus2man(data)[1])


os.execl("./viewer.sh", "")
