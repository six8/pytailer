.. image:: https://travis-ci.org/GreatFruitOmsk/pytailer.svg?branch=master

======
Tailer
======

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
    tailer.tail(open('test.txt', 'rb'), 3)
    # [b'Line 9', b'Line 10', b'Line 11']

Head
----
::

    # Get the first 3 lines of the file
    tailer.head(open('test.txt', 'rb'), 3)
    # [b'Line 1', b'Line 2', b'Line 3']

Follow
------
::

    # Follow the file as it grows
    import time
    for line in tailer.follow(open('test.txt', 'rb')):
        if line is not None:
            print line
        else:
            time.sleep(1)

Follow path
-----------
::

    # Follow the file as it grows and handle file rotation if it occurs
    import time
    for line in tailer.follow_path('test.txt'):
        if line is not None:
            print line
        else:
            time.sleep(1)

Running Tests
=============

Tailer currently only has doctests.

Run tests with nose::

    nosetests --with-doctest tailer

Run tests with doctest::

    python -m doctest -v tailer/__init__.py
