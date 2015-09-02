.. image:: http://img.shields.io/travis/aitjcize/cppman.svg?style=flat
   :target: https://travis-ci.org/aitjcize/cppman
.. image:: http://img.shields.io/pypi/v/cppman.svg?style=flat
   :target: https://pypi.python.org/pypi/cppman
.. image:: http://img.shields.io/pypi/dm/cppman.svg?style=flat
   :target: https://crate.io/packages/cppman

cppman
======
C++ 98/11/14 manual pages for Linux, with source from `cplusplus.com <http://cplusplus.com/>`_ and `cppreference.com <http://cppreference.com/>`_.

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

Note that cppman requires Python 3. Make sure that either ``pip`` is configured for Python 3 installation, your default Python interpeter is version 3 or just use ``pip3`` instead.

2. Arch Linux users can find it on AUR or using `Yaourt <https://wiki.archlinux.org/index.php/Yaourt>`_:

.. code-block:: bash

    $ yaourt -S cppman

or install the git version

.. code-block:: bash

    $ yaourt -S cppman-git

3. Debian / Ubuntu: cppman is available in Debian sid/unstable and Ubuntu vivid.

.. code-block:: bash

    $ sudo apt-get install cppman

FAQ
---
* Q: Can I use the system ``man`` command instead of ``cppman``?
* A: Yes, just execute ``cppman -m true`` and all cached man pages are exposed to the system ``man`` command.  Note: You may want to download all available man pages with ``cppman -c``.

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
