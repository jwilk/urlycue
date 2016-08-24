# Copyright © 2016 Jakub Wilk <jwilk@jwilk.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
the command-line interface
'''

import argparse
import asyncio
import io
import re
import sys
import types

from lib.io import (
    get_encoding,
    open_file,
)
from lib.version import __version__
from lib import web

n_workers = 8

def extract_urls(s):
    '''
    extract URLs from the string
    '''
    return re.compile(
        r'''https?://\w[^\s\\"'<>)\]}#]+'''  # FIXME: this is very simplistic
    ).findall(s)

async def process_url(options, location, url):
    '''
    check the URL
    '''
    what = url
    if options.dry_run:
        status = web.status_ok
    else:
        status = await web.check_url(url)
    if isinstance(status, Exception):
        status = str(status) or repr(status)
    else:
        if status.ok and (not options.verbose):
            return
        if status.location is not None:
            what += ' -> ' + status.location
    (path, n) = location
    print('{path}:{n}: [{status}] {what}'.format(path=path, n=n, status=status, what=what))

async def process_queue(context):
    '''
    check all URLs from the queue
    '''
    while True:
        item = await context.queue.get()
        if item is None:
            return
        (location, url) = item
        await process_url(context.options, location, url)

def extract_urls_from_file(context, path):
    '''
    extract URLs from file
    yield ((path, n), url) tuples
    '''
    encoding = context.options.encoding
    file = open_file(path, encoding=encoding, errors='replace')
    with file:
        for n, line in enumerate(file, 1):
            for url in extract_urls(line):
                location = (file.name, n)
                yield (location, url)

async def queue_files(context, paths):
    '''
    add URLs from files to the queue
    '''
    queue = context.queue
    for path in paths:
        for (location, url) in extract_urls_from_file(context, path):
            await queue.put((location, url))
    for i in range(n_workers):
        del i
        await queue.put(None)

def process_files(options, paths):
    '''
    check all files
    '''
    context = types.SimpleNamespace()
    context.options = options
    context.queue = asyncio.Queue()
    tasks = [queue_files(context, paths)]
    tasks += [process_queue(context) for i in range(n_workers)]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()

class VersionAction(argparse.Action):
    '''
    argparse --version action
    '''

    def __init__(self, option_strings, dest=argparse.SUPPRESS):
        super(VersionAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            help="show program's version information and exit"
        )

    def __call__(self, parser, namespace, values, option_string=None):
        print('{prog} {0}'.format(__version__, prog=parser.prog))
        print('+ Python {0}.{1}.{2}'.format(*sys.version_info))
        parser.exit()

def main():
    '''
    run the program
    '''
    ap = argparse.ArgumentParser(description='URL checker')
    ap.add_argument('--version', action=VersionAction)
    ap.add_argument('--dry-run', action='store_true', help="don't do any connections")
    ap.add_argument('--verbose', action='store_true', help='print also URLs without issues')
    ap.add_argument('files', metavar='FILE', nargs='*', default=['-'],
        help='file to check (default: stdin)')
    options = ap.parse_args()
    options.encoding = encoding = get_encoding()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding, line_buffering=True)
    paths = options.files
    del options.files
    process_files(options, paths)

__all__ = ['main']

# vim:ts=4 sts=4 sw=4 et
