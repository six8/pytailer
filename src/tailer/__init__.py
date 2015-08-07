# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import locale
import os
import re
import sys
import time

from tailer.version import VERSION


__version__ = VERSION


if sys.version_info < (3,):
    range = xrange


class Tailer(object):
    """
    Implements tailing and heading functionality like GNU tail and head
    commands.
    """
    LINE_TERMINATORS = (b'\r\n', b'\n', b'\r')

    def __init__(self, file, read_size=1024, end=False):
        """
        Tailer requires file to be opened in binary mode, otherwise
        the behavior of tell suffers from implementation detail on Windows
        where it may return negative numbers. Per modern Python documentation
        tell returns opaque number for text objects that may not represent
        number of bytes.

        :param file: File-like object opened in binary mode.
        :param read_size: How many bytes to read at once. Affects head and tail calls.
        :param end: Whether to start reading from end.

        :raise ValueError: If file is not open in binary mode.
        """
        if not isinstance(file, io.IOBase) or isinstance(file, io.TextIOBase):
            raise ValueError("io object must be in the binary mode")

        self.read_size = read_size
        self.file = file

        if end:
            self.file.seek(0, io.SEEK_END)

    def splitlines(self, data):
        """
        Split data into lines where lines are separated by LINE_TERMINATORS.

        :param data: Any chunk of binary data.
        :return: List of lines without any characters at LINE_TERMINATORS.
        """
        return re.split(b'|'.join(self.LINE_TERMINATORS), data)

    def read(self, read_size=-1):
        """
        Read given number of bytes from file.
        :param read_size: Number of bytes to read. -1 to read all.
        :return: Number of bytes read and data that was read.
        """
        read_str = self.file.read(read_size)
        return len(read_str), read_str

    def prefix_line_terminator(self, data):
        """
        Return line terminator data begins with or None.
        """
        for t in self.LINE_TERMINATORS:
            if data.startswith(t):
                return t

        return None

    def suffix_line_terminator(self, data):
        """
        Return line terminator data ends with or None.
        """
        for t in self.LINE_TERMINATORS:
            if data.endswith(t):
                return t

        return None

    def seek_next_line(self):
        """
        Seek next line relative to the current file position.

        :return: Position of the line or -1 if next line was not found.
        """
        where = self.file.tell()
        offset = 0

        while True:
            data_len, data = self.read(self.read_size)
            data_where = 0

            if not data_len:
                break

            # Consider the following example: Foo\r | \nBar where " | " denotes current position,
            # 'Foo\r' is the read part and '\nBar' is the remaining part.
            # We should completely consume terminator "\r\n" by reading one extra byte.
            if b'\r\n' in self.LINE_TERMINATORS and data[-1] == b'\r'[0]:
                terminator_where = self.file.tell()
                terminator_len, terminator_data = self.read(1)

                if terminator_len and terminator_data[0] == b'\n'[0]:
                    data_len += 1
                    data += b'\n'
                else:
                    self.file.seek(terminator_where)

            while data_where < data_len:
                terminator = self.prefix_line_terminator(data[data_where:])
                if terminator:
                    self.file.seek(where + offset + data_where + len(terminator))
                    return self.file.tell()
                else:
                    data_where += 1

            offset += data_len
            self.file.seek(where + offset)

        return -1

    def seek_previous_line(self):
        """
        Seek previous line relative to the current file position.

        :return: Position of the line or -1 if previous line was not found.
        """
        where = self.file.tell()
        offset = 0
        line_terminated = False

        while True:
            if offset == where:
                break

            read_size = self.read_size if self.read_size <= where else where
            self.file.seek(where - offset - read_size, io.SEEK_SET)
            data_len, data = self.read(read_size)

            # Consider the following example: Foo\r | \nBar where " | " denotes current position,
            # '\nBar' is the read part and 'Foo\r' is the remaining part.
            # We should completely consume terminator "\r\n" by reading one extra byte.
            if b'\r\n' in self.LINE_TERMINATORS and data[0] == b'\n'[0]:
                terminator_where = self.file.tell()
                if terminator_where > data_len + 1:
                    self.file.seek(where - offset - data_len - 1, io.SEEK_SET)
                    terminator_len, terminator_data = self.read(1)

                    if terminator_data[0] == b'\r'[0]:
                        data_len += 1
                        data = b'\r' + data

                    self.file.seek(terminator_where)

            data_where = data_len

            while data_where > 0:
                terminator = self.suffix_line_terminator(data[:data_where])
                if terminator and offset == 0 and data_where == data_len:
                    # The last character is a line terminator that finishes current line. Ignore it.
                    data_where -= len(terminator)
                    line_terminated = True
                elif terminator:
                    self.file.seek(where - offset - (data_len - data_where))
                    return self.file.tell()
                else:
                    data_where -= 1

            offset += data_len

        return -1
  
    def tail(self, lines=10):
        """
        Return the last lines of the file.
        """
        self.file.seek(0, io.SEEK_END)

        for i in range(lines):
            if self.seek_previous_line() == -1:
                break

        data = self.file.read()

        for t in self.LINE_TERMINATORS:
            if data.endswith(t):
                # Only terminators _between_ lines should be preserved.
                # Otherwise terminator of the last line will be treated as separtaing line and empty line.
                data = data[:-len(t)]
                break

        if data:
            return self.splitlines(data)
        else:
            return []
               
    def head(self, lines=10):
        """
        Return the top lines of the file.
        """
        self.file.seek(0)

        for i in range(lines):
            if self.seek_next_line() == -1:
                break
    
        end_pos = self.file.tell()
        
        self.file.seek(0)
        data = self.file.read(end_pos)

        for t in self.LINE_TERMINATORS:
            if data.endswith(t):
                # Only terminators _between_ lines should be preserved.
                # Otherwise terminator of the last line will be treated as separtaing line and empty line.
                data = data[:-len(t)]
                break

        if data:
            return self.splitlines(data)
        else:
            return []

    def follow(self, delay=1.0, on_delay=None):
        """
        Iterator generator that returns lines as data is added to the file.

        Based on: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/157035
        """
        trailing = True       
        
        while True:
            where = self.file.tell()

            size = os.fstat(self.file.fileno()).st_size
            if where > size:
                # File was truncated.
                where = 0
                self.file.seek(where)

            line = self.file.readline()
            if line:    
                if trailing and line in self.LINE_TERMINATORS:
                    # This is just the line terminator added to the end of the file
                    # before a new line, ignore.
                    trailing = False
                    continue

                terminator = self.suffix_line_terminator(line)
                if terminator:
                    line = line[:-len(terminator)]

                trailing = False
                yield line
            elif on_delay and on_delay():
                break
            else:
                trailing = True
                self.file.seek(where)
                time.sleep(delay)


def tail(file, lines=10, read_size=1024):
    """
    Return the last lines of the file.

    >>> import io
    >>>
    ... with io.open('test_tail.txt', 'w+') as fw:
    ...     with io.open('test_tail.txt', 'rb') as fr:
    ...         _ = fw.write('\\r')
    ...         _ = fw.write('Line 1\\r\\n')
    ...         _ = fw.write('Line 2\\n')
    ...         _ = fw.write('Line 3\\r')
    ...         _ = fw.write('Line 4\\r\\n')
    ...         _ = fw.write('\\n')
    ...         _ = fw.write('\\r\\n')
    ...         _ = fw.write('\\r\\n')
    ...         _ = fw.flush()
    ...         tail(fr, 6, 1)  # doctest: +ELLIPSIS
    [...'Line 2', ...'Line 3', ...'Line 4', ...'', ...'', ...'']
    >>> os.remove('test_tail.txt')
    """
    return Tailer(file, read_size).tail(lines)


def head(file, lines=10, read_size=1024):
    """
    Return the top lines of the file.

    >>> import io
    >>>
    ... with io.open('test_head.txt', 'w+') as fw:
    ...     with io.open('test_head.txt', 'rb') as fr:
    ...         _ = fw.write('\\r\\n')
    ...         _ = fw.write('\\r\\n')
    ...         _ = fw.write('\\r')
    ...         _ = fw.write('Line 1\\r\\n')
    ...         _ = fw.write('Line 2\\r\\n')
    ...         _ = fw.write('Line 3\\r')
    ...         _ = fw.write('Line 4\\r\\n')
    ...         _ = fw.write('\\n')
    ...         _ = fw.write('\\r')
    ...         _ = fw.flush()
    ...         head(fr, 6, 1)  # doctest: +ELLIPSIS
    [...'', ...'', ...'', ...'Line 1', ...'Line 2', ...'Line 3']
    """
    return Tailer(file, read_size).head(lines)


def follow(file, delay=1.0, on_delay=None):
    """
    Generator that returns lines as data is added to the file.

    Returned generator yields bytes.

    >>> import io
    >>> import os
    >>> f = io.open('test_follow.txt', 'w+')
    >>> fo = io.open('test_follow.txt', 'rb')
    >>> generator = follow(fo)
    >>> _ = f.write('Line 1\\n')
    >>> f.flush()
    >>> print(next(generator).decode('utf-8'))
    Line 1
    >>> _ = f.write('Line 2\\n')
    >>> f.flush()
    >>> print(next(generator).decode('utf-8'))
    Line 2
    >>> _ = f.truncate(0)
    >>> _ = f.seek(0)
    >>> _ = f.write('Line 3\\n')
    >>> f.flush()
    >>> print(next(generator).decode('utf-8'))
    Line 3
    >>> f.close()
    >>> fo.close()
    >>> os.remove('test_follow.txt')
    """
    return Tailer(file, end=True).follow(delay, on_delay)


def follow_path(file_path, buffering=-1, encoding=None, errors=None, newline=None, delay=1.0, on_delay=None):
    """
    Similar to follow, but also looks up if inode of file is changed
    e.g. if it was re-created.

    Returned generator yields strings encoded by using encoding.

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
    if encoding is None:
        encoding = locale.getpreferredencoding()

    class FollowPathGenerator(object):
        def __init__(self):
            if os.path.isfile(file_path):
                self.following_file = io.open(file_path, 'rb', buffering, None, errors, newline)
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
                        return next(self.follow_generator).decode(encoding)
                    elif os.path.isfile(file_path):
                        self.following_file = io.open(file_path, 'rb', buffering, None, errors, newline)
                        self.follow_generator = Tailer(self.following_file, end=self.follow_from_end_on_open).follow(delay, self.check_if_inode_changed)
                        self.follow_from_end_on_open = False
                        return next(self.follow_generator).decode(encoding)
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
    try:
        if options.lines > 0:
            with open(filepath, 'rb') as f:
                if options.head:
                    if options.follow:
                        sys.stderr.write('Cannot follow from top of file.\n')
                        sys.exit(1)
                    lines = head(f, options.lines)
                else:
                    lines = tail(f, options.lines)

                for line in lines:
                    print(line.decode(locale.getpreferredencoding()))

        if options.follow:
            for line in follow_path(filepath, delay=options.sleep):
                print(line)
    except KeyboardInterrupt:
        # Escape silently
        pass


def main():
    from argparse import ArgumentParser
    import sys

    parser = ArgumentParser(prog='pytail')

    # group = parser.add_mutually_exclusive_group()

    test_group = parser.add_argument_group("Test")
    test_group.add_argument('--test', dest='test', default=False, action='store_true',
                            help='run some basic tests')

    parser.add_argument('-n', '--lines', dest='lines', default=10, type=int,
                        help='output the last N lines, instead of the last 10')
    parser.add_argument('file', nargs='?', metavar='FILE', help="path to file")

    head_group = parser.add_argument_group('Head')
    head_group.add_argument('-t', '--top', dest='head', default=False, action='store_true',
                            help='output lines from the top instead of the bottom; does not work with follow')

    tail_group = parser.add_argument_group('Tail')
    tail_group.add_argument('-f', '--follow', dest='follow', default=False, action='store_true',
                            help='output appended data as  the  file  grows')
    tail_group.add_argument('-s', '--sleep-interval', metavar='DELAY', dest='sleep', default=1.0, type=float,
                            help='with -f, sleep for approximately DELAY seconds between iterations')

    args = parser.parse_args()

    if args.test:
        _test()
    elif args.file:
        _main(args.file, args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
