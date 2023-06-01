======
Tailer
======

.. image:: https://github.com/six8/pytailer/actions/workflows/python-package.yml/badge.svg
    :target: https://github.com/six8/pytailer/actions/workflows/python-package.yml
    :alt: Build Status

Python tail is a simple implementation of GNU tail and head.

It provides 3 main functions that can be performed on any file-like object that supports ``seek()`` and ``tell()``.

* ``tail`` - read lines from the end of a file
* ``head`` - read lines from the top of a file
* ``follow`` - read lines as a file grows

It also comes with ``pytail``, a command line version offering the same functionality as GNU tail. This can be particularly useful on Windows systems that have no tail equivalent.

- `Tailer on GitHub <http://github.com/six8/pytailer>`_
- `Tailer on Pypi <http://pypi.python.org/pypi/tailer>`_

Installation
============

Install with ``pip`` or ``easy_install``.

::

    pip install tailer

Examples
========

::

  import tailer
  f = open('test.txt', 'w')
  for i in range(11):
      f.write('Line %d\\n' % (i + 1))
  f.close()

Tail
----
::

    # Get the last 3 lines of the file
    tailer.tail(open('test.txt'), 3)
    # ['Line 9', 'Line 10', 'Line 11']

Head
----
::

    # Get the first 3 lines of the file
    tailer.head(open('test.txt'), 3)
    # ['Line 1', 'Line 2', 'Line 3']

Follow
------
::

    # Follow the file as it grows
    for line in tailer.follow(open('test.txt')):
        print line # use print(line) for python3
    

Running Tests
=============

Tailer currently only has doctests.

Run tests with nose::

    nosetests --with-doctest src/tailer

Run tests with doctest::

    python -m doctest -v src/tailer/__init__.py
