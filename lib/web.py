# Copyright © 2016-2024 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
HTTP client
'''

import http
import logging
import ssl
import urllib.parse

import aiohttp

aiohttp_major_ver = int(aiohttp.__version__.split('.', 1)[0])
if aiohttp_major_ver >= 2:
    misc_aiohttp_errors = ()
else:
    misc_aiohttp_errors = (
        aiohttp.errors.DisconnectedError,  # pylint: disable=no-member
        aiohttp.errors.HttpProcessingError,  # pylint: disable=no-member
    )

user_agent = 'urlycue (https://github.com/jwilk/urlycue)'
http_headers = {'User-Agent': user_agent}
redirect_limit = 10

class Status:
    '''
    HTTP response status + location
    '''

    def __init__(self, *, code, location=None):
        self.code = http.HTTPStatus(code)  # pylint: disable=no-value-for-parameter
        self.location = location
        self.temporary_redirect = code in {
            http.HTTPStatus.FOUND,
            http.HTTPStatus.SEE_OTHER,
            http.HTTPStatus.TEMPORARY_REDIRECT,
        }
        self.permanent_redirect = code in {
            http.HTTPStatus.MOVED_PERMANENTLY,
            http.HTTPStatus.PERMANENT_REDIRECT,
        }
        self.redirect = self.temporary_redirect or self.permanent_redirect
        self.ok = self.code == http.HTTPStatus.OK

    def __str__(self):
        hs = self.code
        return f'{hs} {hs.phrase}'  # pylint: disable=missing-format-attribute

status_ok = Status(code=http.HTTPStatus.OK)
assert status_ok.ok

async def _check_url(session, url):
    logger = logging.getLogger('urlycue')
    n_redirects = 0
    redirect_status = True
    while True:
        async with session.head(url, allow_redirects=False) as response:
            location = response.headers.get('Location')
            if location is not None:
                location = urllib.parse.urljoin(url, location)
                if not location.startswith(('http://', 'https://')):
                    return RuntimeError('non-HTTP redirect')
            try:
                status = Status(
                    code=response.status,
                    location=location,
                )
            except ValueError as exc:
                return exc
            if status.redirect:
                n_redirects += 1
                if n_redirects > redirect_limit:
                    return RuntimeError('redirect limit exceeded')
                if redirect_status and status.permanent_redirect:
                    redirect_status = status
                else:
                    redirect_status = None
                logger.debug(f'redirect {url} -> {location}')
                url = location
                continue
            if status.ok and isinstance(redirect_status, Status):
                return redirect_status
            return status
    return status

_url_cache = {}

async def check_url(url, check_cert=True):
    '''
    check the URL
    return an exception or Status object
    '''
    logger = logging.getLogger('urlycue')
    logger.debug(f'start {url}')
    try:
        cached = _url_cache[url]
    except KeyError:
        pass
    else:
        logger.debug(f'cached {url}')
        return cached
    tls_context = ssl.create_default_context()
    if not check_cert:
        tls_context.check_hostname = False
        tls_context.verify_mode = ssl.CERT_NONE
    if aiohttp_major_ver >= 3:
        conn_opts = dict(ssl=tls_context)
    else:
        conn_opts = dict(ssl_context=tls_context)
    connector = aiohttp.connector.TCPConnector(**conn_opts)  # pylint: disable=unexpected-keyword-arg
    try:
        async with aiohttp.client.ClientSession(connector=connector, headers=http_headers) as session:
            status = await _check_url(session, url)
    except aiohttp.ClientOSError as exc:
        rexc = exc
        while rexc is not None:
            if isinstance(rexc, ssl.SSLError):
                break
            rexc = rexc.__cause__
        status = rexc or exc
    except ssl.CertificateError as exc:
        status = exc
    except aiohttp.ClientError as exc:
        status = exc
    except misc_aiohttp_errors as exc:  # pylint: disable=catching-non-exception
        status = exc
    _url_cache[url] = status
    logger.debug(f'done {url}')
    return status

__all__ = [
    'Status',
    'status_ok',
    'check_url',
]

# vim:ts=4 sts=4 sw=4 et
