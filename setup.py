#!/usr/bin/env python

from distutils.core import setup

_package_data = [
        'lib/index.db',
        'lib/pager_vim.sh',
        'lib/pager_less.sh',
        'lib/pager_system.sh',
        'lib/render.sh',
        'lib/cppman.vim'
        ]

_data_files = [
        ('share/doc/cppman', ['README.rst', 'AUTHORS', 'COPYING', 'ChangeLog']),
        ('share/man/man1', ['misc/cppman.1'])
        ]

setup(
        name = 'cppman',
        version = '0.4.6',
        description = 'C++ 98/11/14 manual pages for Linux/MacOS',
        author = 'Wei-Ning Huang (AZ)',
        author_email = 'aitjcize@gmail.com',
        url = 'http://github.com/aitjcize/cppman',
        license = 'GPL',
        packages = ['cppman', 'cppman.formatter'],
        package_data = {'cppman': _package_data},
        data_files = _data_files,
        scripts = ['bin/cppman'],
        install_requires=['beautifulsoup4'],
        classifiers = [
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3 :: Only',
            'Topic :: Software Development :: Documentation',
        ],
)
