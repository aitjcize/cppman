#-*- coding: utf-8 -*-
# 
# Environ.py
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

import os
import sys

from os.path import expanduser, abspath, realpath, dirname, exists

home = expanduser('~')

# If launched from source directory
if not sys.argv[0].startswith('/usr/bin'):
    prefix = dirname(abspath(sys.argv[0]))
    man_dir = home + '/.local/share/man/man3/'
    index_db = prefix + '/../lib/index.db'
    index_db_re = index_db
    viewer = prefix + '/../lib/viewer.sh'
else:
    config_dir = home + '/.config/cppman/'
    try:
        os.mkdir(config_dir)
    except: pass

    index_db_re = config_dir + 'index.db'
    if exists(index_db_re):
        index_db = index_db_re
    else:
        index_db = '/usr/lib/cppman/index.db'

    man_dir = home + '/.local/share/man/man3/'
    viewer = '/usr/lib/cppman/viewer.sh'

# Add ~/.local/share/man to $HOME/.manpath
manpath = '/.local/share/man'
mf = open(realpath(home + '/.manpath'), 'a+')
lines = mf.readlines()

has_path = False
for line in lines:
    if manpath in line:
        has_path = True
        break

if not has_path:
    mf.write('MANDATORY_MANPATH\t%s\n' % realpath(home + manpath))
mf.close()
