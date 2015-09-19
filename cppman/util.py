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

import fcntl
import os
import struct
import termios
import subprocess

from cppman import environ

import bs4


def update_mandb_path():
    """Add ~/.local/share/man to $HOME/.manpath"""
    HOME = os.path.expanduser('~')
    manpath_file = os.path.normpath(os.path.join(HOME, '.manpath'))
    manpath = '.local/share/man'
    lines = []
    try:
        with open(manpath_file, 'r') as f:
            lines = f.readlines()
    except IOError:
        if not environ.config.UpdateManPath:
            return

    has_path = any([manpath in l for l in lines])

    with open(manpath_file, 'w') as f:
        if environ.config.UpdateManPath:
            if not has_path:
                lines.append('MANDATORY_MANPATH\t%s\n' %
                             os.path.normpath(os.path.join(HOME, manpath)))
        else:
            new_lines = []
            for line in lines:
                if manpath not in line:
                    new_lines.append(line)
            lines = new_lines

        f.writelines(lines)


def update_man3_link():
    man3_path = os.path.join(environ.man_dir, 'man3')

    if os.path.lexists(man3_path):
        if os.path.islink(man3_path):
            if os.readlink(man3_path) == environ.config.Source:
                return
            else:
                os.unlink(man3_path)
        else:
            raise RuntimeError("Can't create link since `%s' already exists" %
                               man3_path)

    os.symlink(environ.config.Source, man3_path)


def get_width():
    """Get terminal width"""
    # Get terminal size
    ws = struct.pack("HHHH", 0, 0, 0, 0)
    ws = fcntl.ioctl(0, termios.TIOCGWINSZ, ws)
    lines, columns, x, y = struct.unpack("HHHH", ws)
    width = columns * 39 / 40
    if width >= columns - 2:
        width = columns - 2
    return width


def groff2man(data):
    """Read groff-formated text and output man pages."""
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
    return str(bs4.BeautifulSoup(data, "html.parser"))
