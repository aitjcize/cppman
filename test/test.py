#!/usr/bin/env python

import sys
import os
import os.path
sys.path.insert(0, os.path.normpath(os.getcwd()))

from cppman.formatter import cplusplus, cppreference

cplusplus.func_test()
cppreference.func_test()
