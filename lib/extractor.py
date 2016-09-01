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
URL extraction
'''

import re

def chars(l, r):
    '''
    return {c | l <= c <= r}
    '''
    return {chr(i) for i in range(ord(l), ord(r) + 1)}

def chars_to_re(cs, prefix=''):
    '''
    build regular expression for set of characters
    '''
    return '[{prefix}{chars}]'.format(
        prefix=prefix,
        chars=''.join(re.escape(c) for c in sorted(cs))
    )

c_gen_delims = set(":/?#[]@")
c_sub_delims = set("!$&'()*+,;=")
c_reserved = c_gen_delims | c_sub_delims
c_unreserved = chars('a', 'z') | chars('A', 'Z') | chars('0', '9') | set('-._/~')
c_urly = c_reserved | c_unreserved
c_foreign = chars('\0', '\x7f') - c_urly

regexp = r'\bhttps?://(?:{C}|%[0-9a-fA-F]{{2}})+'.format(
    C=chars_to_re(c_foreign, prefix=r'^\s')
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
    n = {c: url.count(c) for c in '()[]'}
    while r > 0:
        c = url[r]
        if c in ".,;'":
            r -= 1
        elif c == ')' and n['('] < n[')']:
            r -= 1
            n[')'] -= 1
        elif c == ']' and n['['] < n[']']:
            r -= 1
            n[']'] -= 1
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
    for match in regexp.finditer(s):
        l, _ = match.span()
        prefix = s[(l - 1):l]
        url = trim_url(match.group(), prefix=prefix)
        url = strip_fragment(url)
        yield url

__all__ = ['extract_urls']

# vim:ts=4 sts=4 sw=4 et
