#-*- coding: utf-8 -*-
# 
# Environ.py
#
# Copyright (C) 2010 -  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
# All Rights reserved.
#
# This file is part of cppman.
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

from . import Config

HOME = expanduser('~')

man_dir = HOME + '/.local/share/man/man3/'
config_dir = HOME + '/.config/cppman/'
config_file = config_dir + 'cppman.cfg'
cwd = os.getcwd()

config = Config.Config(config_file)

try:
    os.makedirs(config_dir)
except: pass

cwd = cwd[:cwd.find('cppman') + len('cppman')]

# If launched from source directory
if exists(normpath(join(cwd, 'lib/index.db'))):
    index_db = normpath(join(cwd, 'lib/index.db'))
    index_db_re = index_db

    pager_config = normpath(join(cwd, 'lib/cppman.vim'))

    if config.pager == 'vim':
        pager = normpath(join(cwd, 'lib/pager_vim.sh'))
    else:
        pager = normpath(join(cwd, 'lib/pager_less.sh'))
else:
    index_db_re = normpath(join(config_dir, 'index.db'))
    if exists(normpath(join('/usr', 'lib/cppman/index.db'))):
        prefix = '/usr'
    else:
        prefix = '/usr/local'

    index_db = normpath(join(prefix, 'lib/cppman/index.db'))
    index_db = index_db_re if exists(index_db_re) else index_db

    pager_config = normpath(join(prefix, 'lib/cppman/cppman.vim'))

    if config.pager == 'vim':
        pager = normpath(join(prefix, 'lib/cppman/pager_vim.sh'))
    else:
        pager = normpath(join(prefix, 'lib/cppman/pager_less.sh'))


# Add ~/.local/share/man to $HOME/.manpath
def mandb_changed():
    manpath_file = normpath(join(HOME, '.manpath'))
    manpath = '.local/share/man'
    lines = []
    try:
        with open(manpath_file, 'r') as f:
            lines = f.readlines()
    except IOError:
        if not config.UpdateManPath:
            return

    has_path = any([manpath in l for l in lines])

    with open(manpath_file, 'w') as f:
        if config.UpdateManPath:
            if not has_path:
                lines.append('MANDATORY_MANPATH\t%s\n' %
                             normpath(join(HOME, manpath)))
        else:
            new_lines = []
            for line in lines:
                if manpath not in line:
                    new_lines.append(line)
            lines = new_lines

        for line in lines:
            f.write(line)
