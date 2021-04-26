# Copyright © 2016-2021 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
I/O and encodings
'''

import codecs
import io
import sys

def enc_eq(e1, e2):
    '''
    check if two encodings are equal
    '''
    return (
        codecs.lookup(e1).name ==
        codecs.lookup(e2).name
    )

def get_encoding():
    '''
    get locale encoding (from sys.stdout);
    upgrade ASCII to UTF-8
    '''
    locale_encoding = sys.stdout.encoding
    if enc_eq(locale_encoding, 'ASCII'):
        return 'UTF-8'
    else:
        return locale_encoding

def open_file(path, *, encoding, errors):
    '''
    open() with special case for "-"
    '''
    if path == '-':
        return io.TextIOWrapper(
            sys.stdin.buffer,
            encoding=encoding,
            errors=errors,
        )
    else:
        return open(  # pylint: disable=consider-using-with
            path, 'rt',
            encoding=encoding,
            errors=errors,
        )

__all__ = [
    'get_encoding',
    'open_file',
]

# vim:ts=4 sts=4 sw=4 et
