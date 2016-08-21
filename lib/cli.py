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
import functools
import io
import re
import sys
import urllib.request

import werkzeug.urls

from lib.io import (
    get_encoding,
    open_file,
)
from lib.version import __version__

user_agent = 'urlycue (https://github.com/jwilk/urlycue)'
http_headers = {'User-Agent': user_agent}

@functools.lru_cache(maxsize=None)
def check_url(url):
    url = werkzeug.urls.iri_to_uri(url)
    request = urllib.request.Request(url, headers=http_headers, method='HEAD')
    try:
        with urllib.request.urlopen(request):
            pass
    except urllib.error.URLError as exc:
        return exc

def extract_urls(s):
    return re.compile(
        r'''https?://[^\s\\"'>)\]]+'''  # FIXME: this is very simplistic
    ).findall(s)

def process_file(options, file):
    for n, line in enumerate(file, 1):
        for url in extract_urls(line):
            header = '{path}:{n}:'.format(path=file.name, n=n)
            if options.verbose:
                print(header, end=' ')
                if sys.stdout.line_buffering:
                    sys.stdout.flush()
            status = check_url(url)
            if status is None:
                if options.verbose:
                    status = 'OK'
                else:
                    continue
            if not options.verbose:
                print(header, end=' ')
            print('[{status}] {url}'.format(status=status, url=url))

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
    ap.add_argument('--verbose', action='store_true', help='print also URLs without issues')
    ap.add_argument('files', metavar='FILE', nargs='*', default=['-'],
        help='file to check (default: stdin)')
    options = ap.parse_args()
    encoding = get_encoding()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding, line_buffering=sys.stdout.line_buffering)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding, line_buffering=sys.stderr.line_buffering)
    for path in options.files:
        file = open_file(path, encoding=encoding, errors='replace')
        with file:
            process_file(options, file)

__all__ = ['main']

# vim:ts=4 sts=4 sw=4 et
