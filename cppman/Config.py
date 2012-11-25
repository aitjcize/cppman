#-*- coding: utf-8 -*-
# 
# Config.py
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

import configparser
import os

from os.path import dirname, exists

class Config(object):
    def __init__(self, configfile):
        self._configfile = configfile

        if not exists(configfile):
            self.set_default()
        else:
            self._config = configparser.RawConfigParser()
            self._config.read(self._configfile)

    def __getattr__(self, name):
        value = self._config.get('Settings', name)
        return self.parseBool(value)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            self._config.set('Settings', name, value)
            self.store_config()
        self.__dict__[name] = self.parseBool(value)

    def set_default(self):
        """Set config to default."""
        try:
            os.makedirs(dirname(self._configfile))
        except: pass

        self._config = configparser.RawConfigParser()
        self._config.add_section('Settings')
        self._config.set('Settings', 'UpdateManPath', 'false')
        self._config.set('Settings', 'Pager', 'vim')

        with open(self._configfile, 'w') as f:
            self._config.write(f)

    def store_config(self):
        """Store config back to file."""
        try:
            os.makedirs(dirname(self._configfile))
        except: pass

        with open(self._configfile, 'w') as f:
            self._config.write(f)

    def parseBool(self, val):
        if type(val) == str:
            if val.lower() == 'true':
                return True
            elif val.lower() == 'false':
                return False
        return val
