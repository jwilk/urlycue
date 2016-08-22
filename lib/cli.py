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
import ssl
import sys
import types

import aiohttp
import werkzeug.urls

from lib.io import (
    get_encoding,
    open_file,
)
from lib.version import __version__

user_agent = 'urlycue (https://github.com/jwilk/urlycue)'
http_headers = {'User-Agent': user_agent}
n_workers = 8

_url_cache = {}

async def check_url(url):
    url = werkzeug.urls.iri_to_uri(url)
    try:
        return _url_cache[url]
    except KeyError:
        pass
    try:
        async with aiohttp.ClientSession(headers=http_headers) as session:
            async with session.head(url) as response:
                status = response.status
                if status == 200:
                    status = None
    except aiohttp.errors.ClientOSError as exc:
        rexc = exc
        while rexc is not None:
            if isinstance(rexc, ssl.SSLError):
                break
            rexc = rexc.__cause__
        status = rexc or exc
    except ssl.CertificateError as exc:
        status = exc
    _url_cache[url] = status
    return status

def extract_urls(s):
    return re.compile(
        r'''https?://[^\s\\"'<>)\]}]+'''  # FIXME: this is very simplistic
    ).findall(s)

async def process_file(options, file):
    for n, line in enumerate(file, 1):
        for url in extract_urls(line):
            if options.dry_run:
                status = None
            else:
                status = await check_url(url)
            if status is None:
                if options.verbose:
                    status = 'OK'
                else:
                    continue
            print('{path}:{n}: [{status}] {url}'.format(path=file.name, n=n, status=status, url=url))

async def process_path(options, path):
    encoding = options.encoding
    file = open_file(path, encoding=encoding, errors='replace')
    with file:
        return await process_file(options, file)

async def process_queue(context):
    while True:
        url = await context.queue.get()
        if url is None:
            return
        await process_path(context.options, url)

async def queue_files(context, paths):
    for path in paths:
        await context.queue.put(path)
    queue = context.queue
    for i in range(n_workers):
        del i
        await queue.put(None)

def process_files(options, paths):
    context = types.SimpleNamespace()
    context.options = options
    context.queue = asyncio.Queue()
    tasks = [queue_files(context, paths)]
    tasks += [process_queue(context) for i in range(n_workers)]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*tasks))

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
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding, line_buffering=sys.stdout.line_buffering)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding, line_buffering=sys.stderr.line_buffering)
    paths = options.files
    del options.files
    process_files(options, paths)

__all__ = ['main']

# vim:ts=4 sts=4 sw=4 et
