# -*- coding: utf-8 -*-
#
# util.py - Misc utilities
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
import shutil
import struct
import subprocess
import sys
import termios

import bs4
from cppman import environ


def update_mandb_path():
    """Add $XDG_CACHE_HOME/cppman/man to $HOME/.manpath"""
    manpath_file = os.path.join(environ.HOME, ".manpath")
    man_dir = environ.cache_dir
    manindex_dir = environ.manindex_dir

    lines = []

    """ read all lines """
    try:
        with open(manpath_file, 'r') as f:
            lines = f.readlines()
    except IOError:
        return

    """ remove MANDATORY_MANPATH and MANDB_MAP entry """
    lines = [line for line in lines if man_dir not in line]

    with open(manpath_file, 'w') as f:
        if environ.config.UpdateManPath:
            lines.append('MANDATORY_MANPATH\t%s\n' % man_dir)
            lines.append('MANDB_MAP\t\t\t%s\t%s\n' % (man_dir, manindex_dir))

        f.writelines(lines)


def update_man3_link():
    man3_path = os.path.join(environ.cache_dir, 'man3')

    if os.path.lexists(man3_path):
        if os.path.islink(man3_path):
            if os.readlink(man3_path) == environ.config.Source:
                return
            else:
                os.unlink(man3_path)
        else:
            raise RuntimeError("Can't create link since `%s' already exists" %
                               man3_path)
    try:
        os.makedirs(os.path.join(environ.cache_dir, environ.config.Source))
    except Exception:
        pass

    os.symlink(environ.config.Source, man3_path)


def get_width():
    """Get terminal width"""
    # Get terminal size
    columns, lines = shutil.get_terminal_size()
    width = min(columns * 39 // 40, columns - 2)
    return width


def groff2man(data):
    """Read groff-formatted text and output man pages."""
    width = get_width()

    cmd = 'groff -t -Tascii -m man -rLL=%dn -rLT=%dn' % (width, width)
    handle = subprocess.Popen(
        cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    man_text, stderr = handle.communicate(data)
    return man_text


def html2man(data, formatter):
    """Convert HTML text from cplusplus.com to man pages."""
    groff_text = formatter(data)
    man_text = groff2man(groff_text)
    return man_text


def fixupHTML(data):
    return str(bs4.BeautifulSoup(data, "html5lib"))
