# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import os
import re
import sys
import time


if sys.version_info < (3,):
    range = xrange


class Tailer(object):
    """\
    Implements tailing and heading functionality like GNU tail and head
    commands.
    """
    line_terminators = ('\r\n', '\n', '\r')

    def __init__(self, file, read_size=1024, end=False):
        self.read_size = read_size
        self.file = file
        if end:
            self.seek_end()
    
    def splitlines(self, data):
        return re.split('|'.join(self.line_terminators), data)

    def seek_end(self):
        self.seek(0, io.SEEK_END)

    def seek(self, pos, whence=io.SEEK_SET):
        self.file.seek(pos, whence)

    def get_size(self):
        p = self.file.tell()
        self.seek_end()
        s = self.file.tell()
        self.seek(p)
        return s + 1

    def read(self, read_size=None):
        if read_size:
            read_str = self.file.read(read_size)
        else:
            read_str = self.file.read()

        return len(read_str), read_str

    def seek_line_forward(self):
        """\
        Searches forward from the current file position for a line terminator
        and seeks to the charachter after it.
        """
        pos = self.file.tell()

        bytes_read, read_str = self.read(self.read_size)

        start = 0
        if bytes_read and read_str[0] in self.line_terminators:
            # The first charachter is a line terminator, don't count this one
            start += 1

        while bytes_read > 0:          
            # Scan forwards, counting the newlines in this bufferfull
            i = start
            while i < bytes_read:
                if read_str[i] in self.line_terminators:
                    self.seek(pos + i + 1)
                    return self.file.tell()
                i += 1

            pos += self.read_size
            self.seek(pos)

            bytes_read, read_str = self.read(self.read_size)

        return None

    def seek_line(self):
        """\
        Searches backwards from the current file position for a line terminator
        and seeks to the charachter after it.
        """
        pos = end_pos = self.file.tell()

        read_size = self.read_size
        if pos > read_size:
            pos -= read_size
        else:
            pos = 0
            read_size = end_pos

        self.seek(pos)

        bytes_read, read_str = self.read(read_size)

        if bytes_read and read_str[-1] in self.line_terminators:
            # The last charachter is a line terminator, don't count this one
            bytes_read -= 1

            if read_str[-2:] == '\r\n' and '\r\n' in self.line_terminators:
                # found crlf
                bytes_read -= 1

        while bytes_read > 0:          
            # Scan backward, counting the newlines in this bufferfull
            i = bytes_read - 1
            while i >= 0:
                if read_str[i] in self.line_terminators:
                    self.seek(pos + i + 1)
                    return self.file.tell()
                i -= 1

            if pos == 0 or pos - self.read_size < 0:
                # Not enought lines in the buffer, send the whole file
                self.seek(0)
                return None

            pos -= self.read_size
            self.seek(pos)

            bytes_read, read_str = self.read(self.read_size)

        return None
  
    def tail(self, lines=10):
        """\
        Return the last lines of the file.
        """
        self.seek_end()
        end_pos = self.file.tell()

        for i in range(lines):
            if not self.seek_line():
                break

        data = self.file.read(end_pos - self.file.tell() - 1)
        if data:
            return self.splitlines(data)
        else:
            return []
               
    def head(self, lines=10):
        """\
        Return the top lines of the file.
        """
        self.seek(0)

        for i in range(lines):
            if not self.seek_line_forward():
                break
    
        end_pos = self.file.tell()
        
        self.seek(0)
        data = self.file.read(end_pos - 1)

        if data:
            return self.splitlines(data)
        else:
            return []

    def follow(self, delay=1.0, on_delay=None):
        """\
        Iterator generator that returns lines as data is added to the file.

        Based on: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/157035
        """
        trailing = True       
        
        while True:
            where = self.file.tell()

            if where >= self.get_size():
                # File was truncated.
                self.seek(0)

            line = self.file.readline()
            if line:    
                if trailing and line in self.line_terminators:
                    # This is just the line terminator added to the end of the file
                    # before a new line, ignore.
                    trailing = False
                    continue

                if line[-1] in self.line_terminators:
                    line = line[:-1]
                    if line[-1:] == '\r\n' and '\r\n' in self.line_terminators:
                        # found crlf
                        line = line[:-1]

                trailing = False
                yield line
            elif on_delay and on_delay():
                break
            else:
                trailing = True
                self.seek(where)
                time.sleep(delay)

    def __iter__(self):
        return self.follow()

    def close(self):
        self.file.close()


def tail(file, lines=10):
    """\
    Return the last lines of the file.

    >>> from io import StringIO
    >>> f = StringIO()
    >>> for i in range(11):
    ...     _ = f.write('Line %d\\n' % (i + 1))
    >>> tail(f, 3)  # doctest: +ELLIPSIS
    [...'Line 9', ...'Line 10', ...'Line 11']
    """
    return Tailer(file).tail(lines)


def head(file, lines=10):
    """\
    Return the top lines of the file.

    >>> from io import StringIO
    >>> f = StringIO()
    >>> for i in range(11):
    ...     _ = f.write('Line %d\\n' % (i + 1))
    >>> head(f, 3)  # doctest: +ELLIPSIS
    [...'Line 1', ...'Line 2', ...'Line 3']
    """
    return Tailer(file).head(lines)


def follow(file, delay=1.0, on_delay=None):
    """\
    Iterator generator that returns lines as data is added to the file.

    >>> import io
    >>> import os
    >>> f = io.open('test_follow.txt', 'w+')
    >>> fo = io.open('test_follow.txt', 'r')
    >>> generator = follow(fo)
    >>> _ = f.write('Line 1\\n')
    >>> f.flush()
    >>> print(next(generator))
    Line 1
    >>> _ = f.write('Line 2\\n')
    >>> f.flush()
    >>> print(next(generator))
    Line 2
    >>> _ = f.truncate(0)
    >>> _ = f.seek(0)
    >>> _ = f.write('Line 3\\n')
    >>> f.flush()
    >>> print(next(generator))
    Line 3
    >>> f.close()
    >>> fo.close()
    >>> os.remove('test_follow.txt')
    """
    return Tailer(file, end=True).follow(delay, on_delay)


def follow_path(file_path, buffering=-1, encoding=None, errors=None, newline=None, delay=1.0, on_delay=None):
    """\
    Similar to follow, but also looks up if inode of file is changed
    e.g. if it was re-created.

    >>> import io
    >>> import os
    >>> f = io.open('test_follow_path.txt', 'w+')
    >>> generator = follow_path('test_follow_path.txt')
    >>> _ = f.write('Line 1\\n')
    >>> f.flush()
    >>> print(next(generator))
    Line 1
    >>> _ = f.write('Line 2\\n')
    >>> f.flush()
    >>> print(next(generator))
    Line 2
    >>> _ = f.truncate(0)
    >>> _ = f.seek(0)
    >>> _ = f.write('Line 3\\n')
    >>> f.flush()
    >>> print(next(generator))
    Line 3
    >>> f.close()
    >>> os.remove('test_follow_path.txt')
    >>> f = io.open('test_follow_path.txt', 'w+')
    >>> _ = f.write('Line 4\\n')
    >>> f.flush()
    >>> print(next(generator))
    Line 4
    >>> f.close()
    >>> os.remove('test_follow_path.txt')
    """
    class FollowPathGenerator(object):
        def __init__(self):
            if os.path.isfile(file_path):
                self.following_file = io.open(file_path, 'r', buffering, encoding, errors, newline)
                self.follow_generator = Tailer(self.following_file, end=True).follow(delay, self.check_if_inode_changed)
                self.follow_from_end_on_open = False
            else:
                self.following_file = None
                self.follow_generator = None
                self.follow_from_end_on_open = True

            self.should_break = False

        def check_if_inode_changed(self):
            if not os.path.isfile(file_path) or os.stat(file_path).st_ino != os.fstat(self.following_file.fileno()).st_ino:
                return True
            elif on_delay and on_delay():
                self.should_break = True
                return True
            else:
                return False

        def next(self):
            if self.should_break:
                raise StopIteration()

            while True:
                try:
                    if self.follow_generator:
                        return next(self.follow_generator)  # TODO: may raise StopIteration
                    elif os.path.isfile(file_path):
                        self.following_file = io.open(file_path, 'r', buffering, encoding, errors, newline)
                        self.follow_generator = Tailer(self.following_file, end=self.follow_from_end_on_open).follow(delay, self.check_if_inode_changed)
                        self.follow_from_end_on_open = False
                        return next(self.follow_generator)  # TODO: may raise StopIteration
                    elif on_delay and on_delay():
                        # User does not want to wait anymore.
                        self.should_break = True
                        raise StopIteration()
                    else:
                        time.sleep(delay)
                except StopIteration:
                    if self.should_break:
                        raise
                    else:
                        self.following_file.close()
                        self.following_file = None
                        self.follow_generator = None
                        continue

        def __iter__(self):
            return self

        def __next__(self):
            return self.next()

    return FollowPathGenerator()


def _test():
    import doctest
    doctest.testmod()


def _main(filepath, options):
    tailer = Tailer(open(filepath, 'rb'))

    try:
        try:
            if options.lines > 0:
                if options.head:
                    if options.follow:
                        sys.stderr.write('Cannot follow from top of file.\n')
                        sys.exit(1)
                    lines = tailer.head(options.lines)
                else:
                    lines = tailer.tail(options.lines)
        
                for line in lines:
                    print(line)
            elif options.follow:
                # Seek to the end so we can follow
                tailer.seek_end()

            if options.follow:
                for line in tailer.follow(delay=options.sleep):
                    print(line)
        except KeyboardInterrupt:
            # Escape silently
            pass
    finally:
        tailer.close()


def main():
    from optparse import OptionParser
    import sys

    parser = OptionParser(usage='usage: %prog [options] filename')
    parser.add_option('-f', '--follow', dest='follow', default=False, action='store_true',
                      help='output appended data as  the  file  grows')

    parser.add_option('-n', '--lines', dest='lines', default=10, type='int',
                      help='output the last N lines, instead of the last 10')

    parser.add_option('-t', '--top', dest='head', default=False, action='store_true',
                      help='output lines from the top instead of the bottom. Does not work with follow')

    parser.add_option('-s', '--sleep-interval', dest='sleep', default=1.0, metavar='S', type='float',
                      help='with  -f,  sleep  for  approximately  S  seconds between iterations')

    parser.add_option('', '--test', dest='test', default=False, action='store_true',
                      help='Run some basic tests')

    (options, args) = parser.parse_args()

    if options.test:
        _test()
    elif not len(args) == 1:
        parser.print_help()
        sys.exit(1)
    else:
        _main(args[0], options)

if __name__ == '__main__':
    main()
