# Copyright © 2016-2017 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
URL extraction
'''

import re
import urllib.parse

def chars(l, r):
    '''
    return {c | l <= c <= r}
    '''
    return {chr(i) for i in range(ord(l), ord(r) + 1)}

def chars_to_re(cs, prefix=''):
    '''
    build regular expression for set of characters
    '''
    r_cs = str.join('', (re.escape(c) for c in sorted(cs)))
    return f'[{prefix}{r_cs}]'

c_gen_delims = set(":/?#[]@")
c_sub_delims = set("!$&'()*+,;=")
c_reserved = c_gen_delims | c_sub_delims
c_unreserved = chars('a', 'z') | chars('A', 'Z') | chars('0', '9') | set('-._/~')
c_urly = c_reserved | c_unreserved
c_foreign = chars('\0', '\x7F') - c_urly

r_foreign_par = chars_to_re(c_foreign | {'(', ')'}, prefix=r'^\s')
r_foreign = chars_to_re(c_foreign, prefix=r'^\s')
regexp = (
    fr'(?<=[(])https?://(?:{r_foreign_par}|%[0-9a-fA-F]{{2}})+(?=[)])'  # hi, Markdown!
    fr'|\bhttps?://(?:{r_foreign}|%[0-9a-fA-F]{{2}})+'
)
regexp = re.compile(regexp)

def trim_url(url, prefix=''):
    '''
    trim trailing punctuation from the URL
    '''
    if prefix == '<':
        return url
    # this is where practicality beats purity
    if url.endswith("'/"):
        return url[:-2]
    r = len(url) - 1
    brackets = {
        ket: bra
        for bra, ket in {'()', '[]', '⟨⟩'}
    }
    n = {c: url.count(c)
        for item in brackets.items()
        for c in item
    }
    while r > 0:
        c = url[r]
        if c in ".,:;'":
            r -= 1
            continue
        try:
            ket = c
            bra = brackets[ket]
        except KeyError:
            break
        if n[bra] < n[ket]:
            r -= 1
            n[ket] -= 1
            continue
        else:
            break
    return url[:(r + 1)]

def strip_fragment(url):
    '''
    strip fragment from the URL
    '''
    url, _, _ = url.partition('#')
    return url

def extract_urls(s):
    '''
    extract URLs from the string
    '''
    bad_netloc_chars = {':', '$'}
    bad_netloc_re = re.compile(
        '|'.join(re.escape(ch) for ch in bad_netloc_chars)
    )
    for match in regexp.finditer(s):
        l, _ = match.span()
        prefix = s[(l - 1):l]
        url = trim_url(match.group(), prefix=prefix)
        url = strip_fragment(url)
        try:
            netloc = urllib.parse.urlparse(url).netloc
        except ValueError:
            continue
        if netloc and not bad_netloc_re.search(netloc):
            yield url

__all__ = ['extract_urls']

# vim:ts=4 sts=4 sw=4 et
