# Copyright © 2016-2023 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
the command-line interface
'''

import argparse
import asyncio
import atexit
import logging
import sys
import types
import warnings

from .extractor import extract_urls
from .io import (
    open_file,
)
from . import web

__version__ = '0.3.4'

n_workers = 8

async def process_url(options, location, url):
    '''
    check the URL
    return string describing an issue with the URL, or None
    '''
    what = url
    if options.list:
        return url
    check_cert = not options.no_cert_check
    status = await web.check_url(url, check_cert=check_cert)
    if isinstance(status, Exception):
        status = str(status) or repr(status)
    else:
        if status.ok and (not options.verbose):
            return
        if status.location is not None:
            what += ' -> ' + status.location
    (path, n) = location
    return f'{path}:{n}: [{status}] {what}'

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

def extract_urls_from_file(path):
    '''
    extract URLs from file
    yield ((path, n), url) tuples
    '''
    encoding = sys.stdout.encoding
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
        for (location, url) in extract_urls_from_file(path):
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

async def async_process_files(options, paths):
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
    await asyncio.gather(*tasks)

def process_files(options, paths):
    '''
    check all files
    '''
    asyncio.run(async_process_files(options, paths))
    atexit.register(  # https://github.com/aio-libs/aiohttp/issues/1115
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
            help='show version information and exit'
        )

    def __call__(self, parser, namespace, values, option_string=None):
        print(f'{parser.prog} {__version__}')
        print('+ Python {0}.{1}.{2}'.format(*sys.version_info))
        print(f'+ aiohttp {web.aiohttp.__version__}')
        parser.exit()

def setup_logging(*, debug=False):
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
    ap.add_argument('-k', '--no-cert-check', action='store_true', help='disable certificate verification')
    ap.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('files', metavar='FILE', nargs='*', default=['-'],
        help='file to check (default: stdin)')
    options = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    paths = options.files
    del options.files
    setup_logging(debug=options.debug)
    process_files(options, paths)

__all__ = ['main']

# vim:ts=4 sts=4 sw=4 et
