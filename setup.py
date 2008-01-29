from setuptools import setup, find_packages
setup(
    name = "tailer",
    version = "0.2",
    packages = find_packages(),

    # metadata for upload to PyPI
    author = "Michael Thornton",
    author_email = "msthornton@gmail.com",
    description = "Python tail is a simple implementation of GNU tail and head.",
    long_description = """\
======
Tailer
======
Python tail is a simple implementation of GNU tail and head. 

It provides 3 main functions that can be performed on any file-like object that
supports seek() and tell().

* tail - read lines from the end of a file
* head - read lines from the top of a file
* follow - read lines as a file grows

It also comes with pytail, a command line version offering the same 
functionality as GNU tail. This can be particularly useful on Windows systems
that have no tail equivalent.


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
        print line
""",
    license = "GPL",
    keywords = "tail head",
    url = "http://code.google.com/p/pytailer/",

    entry_points = {
        'console_scripts': [
            'pytail = tailer:main',
        ],
    },
    classifiers = [
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Programming Language :: Python',
        'Topic :: System :: Logging',
        'Topic :: Text Processing'
    ]
)