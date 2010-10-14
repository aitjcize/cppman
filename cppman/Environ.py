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
import platform
import sys

from os.path import expanduser, abspath, normpath, dirname, exists, join

HOME = expanduser('~')

man_dir = HOME + '/.local/share/man/man3/'
config_dir = HOME + '/.config/cppman/'
cwd = os.getcwd()

try:
    os.makedirs(config_dir)
except: pass

cwd = cwd[:cwd.find('manpages-cpp') + len('manpages-cpp')]

# If launched from source directory
if exists(normpath(join(cwd, 'lib/viewer.sh'))):
    index_db = normpath(join(cwd, 'lib/index.db'))
    viewer = normpath(join(cwd, 'lib/viewer.sh'))
    index_db_re = index_db
else:
    index_db_re = normpath(join(config_dir, 'index.db'))
    if exists(normpath(join('/usr', 'lib/cppman/viewer.sh'))):
        prefix = '/usr'
    else:
        prefix = '/usr/local'

    index_db = normpath(join(prefix, 'lib/cppman/index.db'))
    viewer = normpath(join(prefix, 'lib/cppman/viewer.sh'))
    index_db = index_db_re if exists(index_db_re) else index_db

# Add ~/.local/share/man to $HOME/.manpath
if 'bsd' not in platform.system().lower():
    manpath = '.local/share/man'
    mf = open(normpath(join(HOME, '.manpath')), 'a+')
    lines = mf.readlines()

    has_path = False
    for line in lines:
        if manpath in line:
            has_path = True
            break

    if not has_path:
        mf.write('MANDATORY_MANPATH\t%s\n' % normpath(join(HOME, manpath)))
    mf.close()
