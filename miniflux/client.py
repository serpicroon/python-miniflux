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

from typing import Optional

import requests

from miniflux.base import _BaseClient, DEFAULT_USER_AGENT
from miniflux.exceptions import (
    ClientError,
    ResourceNotFound,
    AccessForbidden,
    AccessUnauthorized,
    BadRequest,
    ServerError,
)


class Client(_BaseClient):
    """
    Miniflux API synchronous client.
    """

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 30.0,
        api_key: Optional[str] = None,
        user_agent: str = DEFAULT_USER_AGENT,
        session: Optional[requests.Session] = None,
    ):
        """
        Initializes the Miniflux API client.

        Args:
            base_url (str): The base URL of the Miniflux API. Must start with "http://" or "https://".
            username (Optional[str]): The username for basic authentication.
                                      Required if `api_key` is not provided.
            password (Optional[str]): The password for basic authentication.
                                      Required if `api_key` is not provided.
            timeout (float): The timeout for API requests in seconds. Default is 30.0 seconds.
            api_key (Optional[str]): The API key for authentication.
                                     If provided, takes precedence over `username` and `password`.
            user_agent (str): The User-Agent string to use for API requests.
                              Default is "Miniflux Python Client Library".
            session (requests.Session): A custom requests session to use for API requests.

        Raises:
            ValueError: If `base_url` is not a valid URL starting with "http://" or "https://".
            ValueError: If neither `api_key` nor both `username` and `password` are provided.
        """
        super().__init__(base_url, username, password, timeout, api_key, user_agent)

        self._session = session or requests.Session()
        self._session.headers.update({"User-Agent": user_agent})
        if api_key:
            self._session.headers.update({"X-Auth-Token": api_key})
        elif username and password:
            self._session.auth = (username, password)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _handle_error_response(self, response: requests.Response):
        if response.status_code == 404:
            raise ResourceNotFound(response)
        if response.status_code == 403:
            raise AccessForbidden(response)
        if response.status_code == 401:
            raise AccessUnauthorized(response)
        if response.status_code == 400:
            raise BadRequest(response)
        if response.status_code >= 500:
            raise ServerError(response)
        raise ClientError(response)

    def _request(self, method: str, endpoint: str, **kwargs):
        """
        Make an HTTP request using the requests library.

        Args:
            method (str): The HTTP method (get, post, put, delete).
            endpoint (str): The API endpoint.
            **kwargs: Additional arguments to pass to the request method.

        Returns:
            requests.Response: The HTTP response object.
        """
        kwargs.setdefault("timeout", self._timeout)

        method = method.lower()
        if method == "get":
            return self._session.get(endpoint, **kwargs)
        elif method == "post":
            return self._session.post(endpoint, **kwargs)
        elif method == "put":
            return self._session.put(endpoint, **kwargs)
        elif method == "delete":
            return self._session.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    def close(self) -> None:
        """
        Close the underlying session
        """
        self._session.close()
