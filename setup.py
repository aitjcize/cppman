#!/usr/bin/env python

from distutils.core import setup
from DistUtilsExtra.command import *

_data_files = [
	('lib/cppman', ['lib/index.db', 'lib/viewer.sh']),
        ('share/doc',  ['README', 'AUTHORS', 'COPYING', 'Changlog']),
	('share/man/man1', ['misc/cppman.1'])
	]

setup(
	name = 'manpages-cpp',
	version = '0.1.0',
	description = 'C++ man pages generater that generates C++ man pages'
                      'from cplusplus.com',
	author = 'Wei-Ning Huang (AZ)',
	author_email = 'aitjcize@gmail.com',
        url = 'http://github.com/Aitjcize/manpages-cpp',
	license = 'GPL',
    	packages = ['cppman'],
	scripts = ['bin/cppman'],
	data_files = _data_files,
        cmdclass = { "build": build_extra.build_extra }
)
