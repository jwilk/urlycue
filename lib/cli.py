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
import atexit
import io
import logging
import sys
import types
import warnings

from lib.extractor import extract_urls
from lib.io import (
    get_encoding,
    open_file,
)
from lib.version import __version__
from lib import web

n_workers = 8

async def process_url(options, location, url):
    '''
    check the URL
    return string describing an issue with the URL, or None
    '''
    what = url
    if options.list:
        return url
    status = await web.check_url(url)
    if isinstance(status, Exception):
        status = str(status) or repr(status)
    else:
        if status.ok and (not options.verbose):
            return
        if status.location is not None:
            what += ' -> ' + status.location
    (path, n) = location
    return '{path}:{n}: [{status}] {what}'.format(path=path, n=n, status=status, what=what)

async def process_input_queue(context):
    '''
    check all URLs from the queue
    add the results to the output queue
    '''
    input_queue = context.input_queue
    output_queue = context.output_queue
    while True:
        item = await input_queue.get()
        if item is None:
            break
        (j, location, url) = item
        s = await process_url(context.options, location, url)
        await output_queue.put((j, s))
    await output_queue.put(None)

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
    add URLs from files to the input queue
    '''
    queue = context.input_queue
    j = 0
    for path in paths:
        for (location, url) in extract_urls_from_file(context, path):
            await queue.put((j, location, url))
            j += 1
    for i in range(n_workers):
        del i
        await queue.put(None)

async def process_results(context):
    '''
    print results from the output queue in the right order
    '''
    queue = context.output_queue
    done = 0
    todo = {}
    curr = 0
    while done < n_workers:
        item = await queue.get()
        if item is None:
            done += 1
            continue
        (j, s) = item
        assert j not in todo
        todo[j] = s
        while curr in todo:
            s = todo.pop(curr)
            if s is not None:
                print(s)
            curr += 1
    assert not todo, (curr, todo)
    assert queue.empty()

def process_files(options, paths):
    '''
    check all files
    '''
    context = types.SimpleNamespace()
    context.options = options
    context.input_queue = asyncio.Queue()
    context.output_queue = asyncio.Queue()
    tasks = [queue_files(context, paths)]
    tasks += [process_results(context)]
    tasks += [process_input_queue(context) for i in range(n_workers)]
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    finally:
        loop.close()
    atexit.register(  # https://github.com/KeepSafe/aiohttp/issues/1115
        warnings.filterwarnings,
        action='ignore',
        message='^unclosed transport ',
        category=ResourceWarning,
    )

class VersionAction(argparse.Action):
    '''
    argparse --version action
    '''

    def __init__(self, option_strings, dest=argparse.SUPPRESS):
        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            help="show program's version information and exit"
        )

    def __call__(self, parser, namespace, values, option_string=None):
        print('{prog} {0}'.format(__version__, prog=parser.prog))
        print('+ Python {0}.{1}.{2}'.format(*sys.version_info))
        print('+ aiohttp {0}'.format(web.aiohttp.__version__))
        parser.exit()

def setup_logging(debug=False):
    '''
    logging setup
    '''
    logger = logging.getLogger('urlycue')
    formatter = logging.Formatter('* %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if debug:
        logger.setLevel(logging.DEBUG)

def main():
    '''
    run the program
    '''
    ap = argparse.ArgumentParser(description='URL checker')
    ap.add_argument('--version', action=VersionAction)
    ap.add_argument('-l', '--list', action='store_true', help='list all matching URLs')
    ap.add_argument('-v', '--verbose', action='store_true', help='print also URLs without issues')
    ap.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('files', metavar='FILE', nargs='*', default=['-'],
        help='file to check (default: stdin)')
    options = ap.parse_args()
    options.encoding = encoding = get_encoding()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding, line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding, line_buffering=True)
    paths = options.files
    del options.files
    setup_logging(debug=options.debug)
    process_files(options, paths)

__all__ = ['main']

# vim:ts=4 sts=4 sw=4 et
