# -*- coding: utf-8 -*-
#
# config.py
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

import configparser
import os


class Config(object):
    PAGERS = ['vim', 'nvim', 'less', 'system']
    SOURCES = ['cplusplus.com', 'cppreference.com']

    DEFAULTS = {
        'Source': 'cppreference.com',
        'UpdateManPath': 'false',
        'Pager': 'vim'
    }

    def __init__(self, configfile):
        self._configfile = configfile

        if not os.path.exists(configfile):
            self.set_default()
        else:
            self._config = configparser.RawConfigParser()
            self._config.read(self._configfile)

    def __getattr__(self, name):
        try:
            value = self._config.get('Settings', name)
        except configparser.NoOptionError:
            value = self.DEFAULTS[name]
            setattr(self, name, value)
            self._config.read(self._configfile)

        return self.parse_bool(value)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            self._config.set('Settings', name, value)
            self.save()
        self.__dict__[name] = self.parse_bool(value)

    def set_default(self):
        """Set config to default."""
        try:
            os.makedirs(os.path.dirname(self._configfile))
        except:
            pass

        self._config = configparser.RawConfigParser()
        self._config.add_section('Settings')

        for key, val in self.DEFAULTS.items():
            self._config.set('Settings', key, val)

        with open(self._configfile, 'w') as f:
            self._config.write(f)

    def save(self):
        """Store config back to file."""
        try:
            os.makedirs(os.path.dirname(self._configfile))
        except:
            pass

        with open(self._configfile, 'w') as f:
            self._config.write(f)

    def parse_bool(self, val):
        if type(val) == str:
            if val.lower() == 'true':
                return True
            elif val.lower() == 'false':
                return False
        return val
