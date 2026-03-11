# The MIT License (MIT)
#
# Copyright (c) Frederic Guillot
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Miniflux Python Client Library

A Python client library for Miniflux API with both synchronous and asynchronous support.

Example usage (synchronous):
    import miniflux

    client = miniflux.Client("https://miniflux.example.org", api_key="secret")
    feeds = client.get_feeds()

Example usage (asynchronous):
    import asyncio
    import miniflux

    async def main():
        async with miniflux.AsyncClient("https://miniflux.example.org", api_key="secret") as client:
            feeds = await client.get_feeds()

    asyncio.run(main())
"""

from miniflux.client import Client
from miniflux.async_client import AsyncClient
from miniflux.exceptions import (
    ClientError,
    ResourceNotFound,
    AccessForbidden,
    AccessUnauthorized,
    BadRequest,
    ServerError,
)

__all__ = [
    # Clients
    "Client",
    "AsyncClient",
    # Exceptions
    "ClientError",
    "ResourceNotFound",
    "AccessForbidden",
    "AccessUnauthorized",
    "BadRequest",
    "ServerError",
]
