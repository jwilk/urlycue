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
    'open_file',
]

# vim:ts=4 sts=4 sw=4 et
