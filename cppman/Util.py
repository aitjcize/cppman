#-*- coding: utf-8 -*-
#
# Util.py - Misc utilities
#
# Copyright (C) 2010 - 2014  Wei-Ning Huang (AZ) <aitjcize@gmail.com>
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

import fcntl
import struct
import termios

from posixpath import expanduser, normpath, join

from Environ import config

def update_mandb_path():
    """Add ~/.local/share/man to $HOME/.manpath"""
    HOME = expanduser('~')
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

def get_width():
    """Get terminal width"""
    # Get terminal size
    ws = struct.pack("HHHH", 0, 0, 0, 0)
    ws = fcntl.ioctl(0, termios.TIOCGWINSZ, ws)
    lines, columns, x, y = struct.unpack("HHHH", ws)
    width = columns * 39 / 40
    if width >= columns -2: width = columns -2
    return width
