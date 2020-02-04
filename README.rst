.. image:: http://img.shields.io/travis/aitjcize/cppman.svg?style=flat
   :target: https://travis-ci.org/aitjcize/cppman
.. image:: http://img.shields.io/pypi/v/cppman.svg?style=flat
   :target: https://pypi.python.org/pypi/cppman
.. image::  https://img.shields.io/github/downloads/aitjcize/cppman/total.svg
   :target: https://pypi.python.org/pypi/cppman#downloads

cppman
======
C++ 98/11/14/17/20 manual pages for Linux, with source from `cplusplus.com <http://cplusplus.com/>`_ and `cppreference.com <https://cppreference.com/>`_.

.. image:: https://raw.github.com/aitjcize/cppman/master/wiki/screenshot.png

Features
--------
* Supports two backends (switch it with ``cppman -s``):

  + `cplusplus.com <http://cplusplus.com/>`_
  + `cppreference.com <http://cppreference.com/>`_

* Syntax highlighting support for sections and example source code.
* Usage/Interface similar to the 'man' command
* Hyperlink between manpages (only available when pager=vim)

  + Press ``Ctrl-]`` when cursor is on keyword to go forward and ``Ctrl-T`` to go backward.
  + You can also double-click on keyword to go forward and right-click to go backward.

* Frequently update to support `cplusplus.com <http://cplusplus.com/>`_.

Demo
----
Using vim as pager

.. image:: https://raw.github.com/aitjcize/cppman/master/wiki/demo.gif

Installation
------------
1. Install from PyPI:

.. code-block:: bash

    $ pip install cppman

Note that cppman requires Python 3. Make sure that either ``pip`` is configured for Python 3 installation, your default Python interpreter is version 3 or just use ``pip3`` instead.

2. Arch Linux users can find it on AUR or using `Trizen <https://wiki.archlinux.org/title/Trizen>`_:

.. code-block:: bash

    $ trizen -S cppman

or install the git version

.. code-block:: bash

    $ trizen -S cppman-git

3. Debian / Ubuntu: cppman is available in Debian sid/unstable and Ubuntu vivid.

.. code-block:: bash

    $ sudo apt-get install cppman

4. MacOS X: cppman is available in Homebrew and MacPorts.

.. code-block:: bash

    $ brew install cppman

or

.. code-block:: bash

    $ sudo port install cppman

Package Maintainers
-------------------
* Arch Linux: myself
* Debian: `czchen <https://github.com/czchen>`_
* Gentoo: `rindeal <https://github.com/rindeal>`_
* MacPorts: `eborisch <https://github.com/eborisch>`_

FAQ
---
* Q: Can I use the system ``man`` command instead of ``cppman``?
* A: Yes, just execute ``cppman -m true`` and all cached man pages are exposed to the system ``man`` command.  Note: You may want to download all available man pages with ``cppman -c``.
* Q: Why is bash completion is not working properly with ``::``?
* A: It is because bash treats ``:`` like a white space. To fix this add ``export COMP_WORDBREAKS=" /\"\'><;|&("`` to your ``~/.bashrc``.

Bugs
----
* Please report bugs / mis-formatted pages to the github issue tracker.

Contributing
------------
1. Fork it
2. Create your feature branch (``git checkout -b my-new-feature``)
3. Commit your changes (``git commit -am 'Add some feature'``)
4. Push to the branch (``git push origin my-new-feature``)
5. Create new Pull Request

Notes
-----
* manpages-cpp is renamed to cppman since September 19, 2012
