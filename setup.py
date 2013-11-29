#!/usr/bin/env python

from distutils.core import setup

_package_data = ['lib/index.db', 'lib/pager_vim.sh', 'lib/pager_less.sh',
                 'lib/render.sh', 'lib/cppman.vim']
_data_files = [
        ('share/doc/cppman', ['README.rst', 'AUTHORS', 'COPYING', 'ChangeLog']),
        ('share/man/man1', ['misc/cppman.1'])
        ]

setup(
        name = 'cppman',
        version = '0.3.1',
        description = 'C++ man pages generater that generates C++ man pages'
                      'from cplusplus.com',
        author = 'Wei-Ning Huang (AZ)',
        author_email = 'aitjcize@gmail.com',
        url = 'http://github.com/Aitjcize/cppman',
        license = 'GPL',
        packages = ['cppman'],
        package_data = {'cppman': _package_data},
        data_files = _data_files,
        scripts = ['bin/cppman']
)
