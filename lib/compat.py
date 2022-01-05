# Copyright © 2021-2022 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
compatibility shims
'''

import asyncio
import types
import sys

if sys.version_info < (3, 7):

    compat_asyncio = types.ModuleType('asyncio/compat')
    compat_asyncio.__dict__.update(asyncio.__dict__)

    def asyncio_run(main):
        '''
        execute the coroutine and return the result
        '''
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main)
        loop.close()
    compat_asyncio.run = asyncio_run
    del asyncio_run

    compat_asyncio.create_task = asyncio.ensure_future

    asyncio = compat_asyncio

__all__ = ['asyncio']

# vim:ts=4 sts=4 sw=4 et
