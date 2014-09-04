.. image:: http://img.shields.io/travis/aitjcize/cppman.svg
   :target: https://travis-ci.org/aitjcize/cppman
.. image:: http://img.shields.io/pypi/v/cppman.svg
   :target: https://pypi.python.org/pypi/cppman
.. image:: http://img.shields.io/pypi/dm/cppman.svg
   :target: https://crate.io/packages/cppman

cppman
======
C++ 98/11 manual pages for Linux, with source from `cplusplus.com <http://cplusplus.com/>`_.

.. image:: https://raw.github.com/aitjcize/cppman/master/wiki/screenshot.png

Features
--------
* Syntax highlighting support for sections and example source code.
* Usage/Interface simliar to the 'man' command
* Hyperlink between manpages (only available when pager=vim)

  + Press ``Ctrl-]`` when cursor is on keyword to go forward and ``Ctrl-T`` to go backward.
  + You can also double-click on keyword to go forward.

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

2. Arch Linux users can find it on AUR or using `Yaourt <https://wiki.archlinux.org/index.php/Yaourt>`_:

.. code-block:: bash

    $ yaourt -S cppman

or install the git version

.. code-block:: bash

    $ yaourt -S cppman-git

3. Ubuntu/Debian PPA

.. code-block:: bash

    $ sudo add-apt-repository ppa:cppman/cppman-daily
    $ sudo apt-get update
    $ sudo apt-get install cppman

Thanks `czchen <https://github.com/czchen>`_ for maintaining the package.

Bugs
----
* Please report bugs / mis-formatted pages to the github issure tracker.

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
