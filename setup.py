#!/usr/bin/env python

from distutils.core import setup

_package_data = [
        'lib/index.db',
        'lib/pager.sh',
        'lib/cppman.vim'
        ]

_data_files = [
        ('share/doc/cppman', ['README.rst', 'AUTHORS', 'COPYING', 'ChangeLog']),
        ('share/man/man1', ['misc/cppman.1']),
        ('share/bash-completion/completions', ['misc/completions/cppman.bash']),
        ('share/zsh/vendor-completions/', ['misc/completions/zsh/_cppman']),
        ('share/fish/vendor_completions.d/', ['misc/completions/fish/cppman.fish'])
        ]

setup(
        name = 'cppman',
        version = '0.5.5',
        description = 'C++ 98/11/14/17/20 manual pages for Linux/MacOS',
        author = 'Wei-Ning Huang (AZ)',
        author_email = 'aitjcize@gmail.com',
        url = 'https://github.com/aitjcize/cppman',
        license = 'GPL',
        packages = ['cppman', 'cppman.formatter'],
        package_data = {'cppman': _package_data},
        data_files = _data_files,
        scripts = ['bin/cppman'],
        install_requires=['beautifulsoup4', 'html5lib'],
        classifiers = [
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3 :: Only',
            'Topic :: Software Development :: Documentation',
        ],
)
