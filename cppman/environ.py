# -*- coding: utf-8 -*-
#
# environ.py
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

import os

from cppman import get_lib_path
from cppman.config import Config

HOME = os.environ["HOME"]

XDG_CACHE_HOME = os.getenv("XDG_CACHE_HOME", os.path.join(HOME, ".cache"))
XDG_CONFIG_HOME = os.getenv("XDG_CONFIG_HOME", os.path.join(HOME, ".config"))

cache_dir = os.path.join(XDG_CACHE_HOME, 'cppman')
manindex_dir = os.path.join(cache_dir, 'manindex')
config_dir = os.path.join(XDG_CONFIG_HOME, 'cppman')
config_file = os.path.join(config_dir, 'cppman.cfg')

config = Config(config_file)

try:
    os.makedirs(cache_dir)
    os.makedirs(manindex_dir)
    os.makedirs(config_dir)
    update_man3_link()
except:
    pass

index_db_re = os.path.join(cache_dir, 'index.db')

index_db = index_db_re if os.path.exists(index_db_re) \
    else get_lib_path('index.db')

pager = config.Pager
pager_config = get_lib_path('cppman.vim')
pager_script = get_lib_path('pager.sh')

source = config.Source
if source not in config.SOURCES:
    source = config.SOURCES[0]
    config.Source = source
