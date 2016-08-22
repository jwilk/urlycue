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
HTTP client
'''

import http
import ssl

import aiohttp
import werkzeug.urls

user_agent = 'urlycue (https://github.com/jwilk/urlycue)'
http_headers = {'User-Agent': user_agent}

_url_cache = {}

async def check_url(url):
    '''
    check the URL
    return http.HTTPStatus or an exception
    '''
    url = werkzeug.urls.iri_to_uri(url)
    try:
        return _url_cache[url]
    except KeyError:
        pass
    try:
        async with aiohttp.ClientSession(headers=http_headers) as session:
            async with session.head(url) as response:
                status = response.status
                try:
                    status = http.HTTPStatus(status)  # pylint: disable=no-value-for-parameter
                except ValueError as exc:
                    status = exc
    except aiohttp.errors.ClientOSError as exc:
        rexc = exc
        while rexc is not None:
            if isinstance(rexc, ssl.SSLError):
                break
            rexc = rexc.__cause__
        status = rexc or exc
    except ssl.CertificateError as exc:
        status = exc
    except aiohttp.errors.ClientResponseError as exc:
        status = exc
    _url_cache[url] = status
    return status

__all__ = ['check_url']

# vim:ts=4 sts=4 sw=4 et